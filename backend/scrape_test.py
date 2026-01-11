import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from collections import Counter
import spacy
from urllib.parse import urlparse
import time
import threading
import concurrent.futures

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

ddg = DDGS()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

ALLOWED_DOMAINS = [
    "travel",
    "guide",
    "visit",
    "blog",
    "food",
    ""
]

ALLOWED_VIDEO_DOMAINS = [
    ""
]

# Words/entities we NEVER want as destinations
GENERIC_BLACKLIST = {
    "Italy", "Europe", "Asia", "Africa", "Greece",
    "Honeymoon", "Travel", "Tourism", "Tripadvisor"
}

def build_queries(destination, vibe):
    """Generate vibe-specific search queries"""
    queries = {
        "chill": [
            f"parks, gardens, nature, spas, massages, peaceful places to visit in {destination}"
        ],
        "foodie": [
            f"restaurants, cafes, streetfood, food markets, food tours, food festivals to visit in {destination}"
        ],
        "adventurous": [
            f"things to do in {destination} related to sightseeing, tours, best attractions, theme parks,must-do activities"
        ],
        "nightlife": [
            f"bars, clubs, music venues, nightlife spots to visit in {destination}",
        ],
        "cultural": [
            f"museums, temples, art galleries, cultural landmarks to visit in {destination}",
        ]
    }
    
    return queries.get(vibe, [f"things to do in {destination}"])


def is_allowed_domain(url):
    """Check if domain is allowed for scraping"""
    domain = urlparse(url).netloc.lower()
    return any(allowed in domain for allowed in ALLOWED_DOMAINS)

def is_allowed_video_domain(url):
    """Check if domain is allowed for video scraping"""
    domain = urlparse(url).netloc.lower()
    return any(allowed in domain for allowed in ALLOWED_VIDEO_DOMAINS)



def search_official_website(destination):
    query = f"official booking/reservation website for {destination}"
    result = ddg.text(query, max_results=1)
    return result[0].get('href') or result[0].get('link')


def search_article_urls(query, max_results=50):
    """Search and filter for scrapeable article URLs"""
    urls = []
    
    print(f"  Searching: '{query}'")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=50))
            
            for r in results:
                url = r.get('href') or r.get('link')
                title = r.get('title', '')
                
                if url and is_allowed_domain(url):
                    urls.append({'url': url, 'title': title})
                    print(f"     {title[:60]}")
                    
                    if len(urls) >= max_results:
                        break
        
        time.sleep(1)
        
    except Exception as e:
        print(f"      Search error: {e}")
    
    return urls


def extract_video_urls(query, max_results=20):
    urls = []
    
    results = ddg.videos(query, max_results=max_results)
    
    for i, result in enumerate(results, 1):
        url = result.get('content')
        if url and is_allowed_video_domain(url):
            urls.append(url)
            print(f"     {url[:60]}")
        
        time.sleep(1)
        
    return urls


def extract_query_entities(query):
    """Extract location entities from query to filter them out"""
    doc = nlp(query)
    query_places = set()
    
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            query_places.add(ent.text.strip().lower())
            # query_places.add(ent.text.strip().title())
    
    return query_places


def extract_venues_from_text(text, destination, query_blacklist):
    """Use spaCy NLP to extract venue names from article text"""
    doc = nlp(text)
    venues = []
    
    for ent in doc.ents:
        # Look for Places, Facilities, Organizations
        if ent.label_ in ("GPE", "LOC", "FAC", "ORG"):
            name = ent.text.strip().title()
            name_lower = name.lower()
            
            # Filter out generic locations
            if name in GENERIC_BLACKLIST:
                continue
            
            # Filter out query locations (e.g., "Santa Barbara")
            if name_lower in query_blacklist or name in query_blacklist:
                continue
            
            # Filter if any word from destination is in the venue name
            # This catches "Santa Barbara's", "Santa Barbara Zoo", etc.
            dest_words = set(destination.lower().split())
            name_words = set(name_lower.split())
            if dest_words.intersection(name_words):
                continue
            
            # Filter out overly generic terms
            if name_lower in ['the pacific ocean', 'pacific ocean', 'the channel islands', 'channel islands']:
                continue
            
            # Filter single words (usually not specific venues)
            if len(name.split()) < 2:
                continue
            
            # Filter all-caps (usually abbreviations)
            if name.isupper():
                continue
            
            # Filter out common article words
            if any(word in name_lower for word in ['guide', 'tips', 'best', 'top']):
                continue
            
            # Filter out possessives that slipped through
            if "'s" in name or "'S" in name:
                continue
            
            venues.append(name)
    
    return venues


def scrape_article_for_venues(url, destination, query_blacklist):
    """Scrape an article and extract venue names"""
    venues = []
    
    try:
        print(f"    Scraping: {url[:60]}...")
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find main content (article, main, or body)
        content = soup.find("article") or soup.find("main") or soup.find("body")
        
        if content:
            # Extract text
            text = content.get_text(" ", strip=True)
            
            # Use NLP to extract venues
            venues = extract_venues_from_text(text, destination, query_blacklist)
            
            print(f"      Found {len(venues)} potential venues")
        
    except Exception as e:
        print(f"       Error: {str(e)[:60]}")
    
    return venues


async def collect_venues(destination, vibe):
    """Main venue collection pipeline"""
    print(f" Searching for {vibe} venues in {destination}...\n")
    
    queries = build_queries(destination, vibe)
    all_venues = []
    
    for query in queries:
        # Extract query entities to filter out
        query_blacklist = extract_query_entities(query)
        query_blacklist.add(destination.lower())
        query_blacklist.add(destination.title())
        
        # Search for article URLs
        articles = search_article_urls(query, max_results=15)
        article_urls = [article['url'] for article in articles]
        
        videos = extract_video_urls(query, max_results=10)
            
        destinations = [destination] * len(article_urls)
        query_blacklists = [query_blacklist] * len(article_urls)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            venues_results = list(executor.map(scrape_article_for_venues, article_urls, destinations, query_blacklists))
            for venues_list in venues_results:
                all_venues.extend(venues_list)
        print()
    
    venue_counts = Counter(all_venues)
    
    ranked_venues = [
        {
            "name": name,
            "type": "activity",
            "score": count
        }
        for name, count in venue_counts.most_common(30)
    ]
    
    print(f" Extracted {len(ranked_venues)} unique venues (ranked by mentions)\n")
    
    print("Top venues found (ranked by how often they were mentioned):")
    for v in ranked_venues[:10]:
        print(f"   {v['name']} - mentioned {v['score']}x across articles")
    print()
    
    # return ranked_venues
    for video in videos:
        print(f"     {video[:60]}")
    return videos


if __name__ == "__main__":
    top_places = collect_venues("Tokyo", "adventurous")

    print("\nTop destinations:")
    for venue in top_places:
        print(f"{venue['name']} ({venue['score']})")
    # print(search_official_website("Eiffel Tower"))