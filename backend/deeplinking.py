import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def scrape_google_hotels(destination, checkin, checkout, adults):
    base_url = "https://www.google.com/travel/hotels"
    query = f"hotels in {destination}"
    params = {'q': query,
              'checkin': checkin,
              'checkout': checkout,
              'adults': adults}
    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    hotels = []
    
    print(f"  Scraping Google Hotels: {search_url[:60]}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            await page.goto(search_url, timeout=60000)
            
            print("  - Scrolling to load cards...")
            for _ in range(3):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(1000)

            print("  - extracting data...")
            await page.wait_for_selector('h2, h3', timeout=10000)
            
            headings = await page.locator('div[role="heading"], h2, h3').all()
            
            count = 0
            for heading in headings:
                if count >= 10: break
                
                name = await heading.inner_text()
                name = name.strip()
                if not name: continue
                
                try:
                    card_text = await heading.locator("xpath=../../..").inner_text()
                    
                    if "$" in card_text:
                        price_match = re.search(r'\$(\d+)', card_text)
                        
                        if price_match:
                            price = int(price_match.group(1))
                            rating = 4.5 
                            if "4." in card_text:
                                rating = 4.0
                                
                            address = ""
                            lines = card_text.split('\n')
                            for i, line in enumerate(lines):
                                if name in line and i + 1 < len(lines):
                                    potential_address = lines[i + 1].strip()
                                    if potential_address and '$' not in potential_address and 'rating' not in potential_address.lower():
                                        address = potential_address
                                        break
                                
                            hotels.append({"name": name, "price": price, "rating": rating, "address": address})
                            print(f"    ✓ Found: {name} (${price}) - {address}")
                            count += 1
                except:
                    continue

        except Exception as e:
            print(f" Scraping error: {e}")
            await page.screenshot(path="error_screenshot.png")
            print("   Saved 'error_screenshot.png' - check this image!")

        await browser.close()
        
    return hotels


def pick_winner(hotels):
    best_hotel = None
    best_score = -1
    
    print("\n Calculating Value Scores:")
    print(f"{'Hotel':<20} | {'Price':<5} | {'Rating':<5} | {'Score'}")
    print("-" * 50)
    
    for h in hotels:
        if h['rating'] < 4.0:
            continue
            
        score = (h['rating'] ** 2) / h['price'] * 100
        
        print(f"{h['name']:<20} | ${h['price']:<4} | {h['rating']:<5} | {score:.2f}")
        
        if score > best_score:
            best_score = score
            best_hotel = h
            
    return best_hotel


def generate_booking_search_link(hotel_name, checkin, checkout, adults):
    base_url = "https://www.booking.com/searchresults.html"
    
    params = {
        'ss': hotel_name,
        'checkin': checkin,
        'checkout': checkout,
        'group_adults': adults,
        'no_rooms': 1,
        'group_children': 0
    }
    
    encoded = urllib.parse.urlencode(params)
    return f"{base_url}?{encoded}"


async def run(address, checkin, checkout, adults):
    result = []
    candidates = await scrape_google_hotels(address, checkin, checkout, adults)
    winner = pick_winner(candidates)
    if winner:
        print(f"\n WINNER: {winner['name']} (Best balance of Price/Rating)")
        
        final_link = generate_booking_search_link(winner['name'], checkin, checkout, adults)
        print(f" Booking Link: {final_link}")
        return [final_link, winner['name'], winner['address']]
    else:
        print("No suitable hotels found.")
        return None


# --- RUN IT ---
# For Jupyter/IPython (already has event loop):
# await run("705 Cornish Dr, San Diego, CA 92107", "2026-02-06", "2026-02-07", 2)

# For regular Python script execution:
if __name__ == "__main__":
    asyncio.run(run("705 Cornish Dr, San Diego, CA 92107", "2026-02-06", "2026-02-07", 2))