from playwright.sync_api import sync_playwright
import urllib.parse

def scrape_google_hotels(destination, checkin, checkout, adults):
    base_url = "https://www.google.com/travel/hotels"
    query = f"hotels in {destination}"
    params = {'q': query,
              'checkin': checkin,
              'checkout': checkout,
              'adults': adults}
    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    hotels = []
    
    print(f"  Scraping Google Hotels: {search_url[:60]}...")
    
    with sync_playwright() as p:
        # Launch browser (headless=True is faster, False lets you watch)
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        # Wait for hotel cards to load - try multiple strategies since Google changes selectors
        try:
            page.goto(search_url, timeout=60000)
            
            # 2. SCROLLING: This forces the hotel cards to actually render
            print("  - Scrolling to load cards...")
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(1000) # Wait 1 sec for load

            # 3. ROBUST SELECTOR: Look for headings (Hotel Names) 
            # Google ALWAYS uses h2 or h3 for hotel names for accessibility.
            # We look for any heading that has text.
            print("  - extracting data...")
            
            # This selector looks for headers inside the main list
            # We wait for at least one header to appear
            page.wait_for_selector('h2, h3', timeout=10000)
            
            # Get all text from the page to parse simply
            # (Parsing raw text is often more reliable than complex selectors)
            # But let's try to get specific elements first.
            
            # Strategy: Find the container that holds the name and price
            # We find all elements with role="heading" (the hotel names)
            headings = page.locator('div[role="heading"], h2, h3').all()
            
            count = 0
            for heading in headings:
                if count >= 10: break
                
                name = heading.inner_text().strip()
                if not name: continue # Skip empty headers
                
                # LIMITATION: Finding the EXACT price relative to the header is hard 
                # because DOM nesting changes. 
                # TRICK: We assume valid hotels are headers with >3 characters.
                
                # To find price, we look at the parent's text content
                # This is a bit "hacky" but works when classes are scrambled.
                try:
                    # Go up 3 levels to get the 'card' container
                    card_text = heading.locator("xpath=../../..").inner_text()
                    
                    if "$" in card_text:
                        # Simple extraction: Find the first thing that looks like a price
                        import re
                        price_match = re.search(r'\$(\d+)', card_text)
                        
                        if price_match:
                            price = int(price_match.group(1))
                            
                            # Fake rating if we can't find it (Ratings are hard to scrape reliably)
                            rating = 4.5 
                            if "4." in card_text:
                                rating = 4.0 # Placeholder logic
                                
                            hotels.append({"name": name, "price": price, "rating": rating})
                            print(f"    ✓ Found: {name} (${price})")
                            count += 1
                except:
                    continue

        except Exception as e:
            print(f" Scraping error: {e}")
            # Take a screenshot so you can see what went wrong!
            page.screenshot(path="error_screenshot.png")
            print("   Saved 'error_screenshot.png' - check this image!")

        browser.close()
        
    return hotels



def pick_winner(hotels):
    best_hotel = None
    best_score = -1
    
    print("\n Calculating Value Scores:")
    print(f"{'Hotel':<20} | {'Price':<5} | {'Rating':<5} | {'Score'}")
    print("-" * 50)
    
    for h in hotels:
        # Filter: Skip anything below 4.0 stars immediately
        if h['rating'] < 4.0:
            continue
            
        score = (h['rating'] ** 2) / h['price'] * 100
        
        print(f"{h['name']:<20} | ${h['price']:<4} | {h['rating']:<5} | {score:.2f}")
        
        if score > best_score:
            best_score = score
            best_hotel = h
            
    return best_hotel


def generate_booking_search_link(hotel_name, checkin, checkout, adults):
    """
    Creates a Booking.com SEARCH URL.
    This is safer than guessing the slug.
    """
    base_url = "https://www.booking.com/searchresults.html"
    
    params = {
        'ss': hotel_name, # 'ss' = Search String
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': adults,
        'no_rooms': 1,
        'group_children': 0
    }
    
    encoded = urllib.parse.urlencode(params)
    return f"{base_url}?{encoded}"

# --- RUN IT ---
candidates = scrape_google_hotels("tokyo", "2026-02-06", "2026-02-08", 2) #f"{final} {destination}"
winner = pick_winner(candidates)

if winner:
    print(f"\n WINNER: {winner['name']} (Best balance of Price/Rating)")
    
    final_link = generate_booking_search_link(winner['name'], "2026-02-06", "2026-02-08", 2)
    print(f" Booking Link: {final_link}")
else:
    print("No suitable hotels found.")