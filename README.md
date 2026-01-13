
## Inspiration
We all spend hours scrolling through beautiful travel Reels and TikToks, only to realize that turning that "vibe" into a real plan is a nightmare. Current travel apps are either static directories or generic LLM chat interfaces that hallucinate closed venues or geographically impossible routes. We wanted to build Reel-to-Real to bridge the gap between social media inspiration and executable reality, taking you from a screen to the streets in under two minutes.

## What it does
Reel-To-Real is an end-to-end autonomous travel agent. You provide a destination, a vibe (e.g., "adventurous," "hidden gems"), and a budget. The system concurrently scrapes live travel data, extracts venues using NLP, parses videos for location and attractions using TwelveLabs, and validates them for quality using Google Gemini. It then runs a modified Traveling Salesman Problem (TSP) algorithm to build a logically sequenced, time-aware itinerary complete with maps, travel times, and meal breaks. 
It ultimately provides "ready-to-reserve" actions with all the manual data (location, date, number of people, etc.) already filled out for you. 

## How we built it
**The Brain:** We engineered a high-concurrency FastAPI backend to handle the heavy load of CPU-intensive SpaCy tasks and 15+ external API calls. By implementing multithreading to execute these processes in parallel, we slashed the runtime from several minutes to just seconds, enabling a near real-time user experience. We also didn't want static results, so we implemented deep linking for every generated itinerary for the "ready-to-reserve" actions. For the research, we used DuckDuckGo Search library to find websites and videos related to the users' travel wishes, and used BeautifulSoup to web scrape the websites and TwelveLabs to parse the videos that DuckDuckGo found. Finally, we aggregated the data to identify high-frequency overlaps. By cross-referencing results from both text and video sources, we prioritized attractions that appeared most often—using multi-source consensus as a reliability metric to ensure users get verified, popular locations rather than random outliers.

**The Logic:** We used spaCy for NLP entity extraction and Google Gemini 2.5 Flash as a validation layer to ensure every recommendation is high-quality.

**The Math:** We implemented a custom routing algorithm that accounts for "time windows" (opening/closing hours) and geospatial distance using Geoapify and OpenStreetMap.

**The Video Pipeline:** We integrated Twelve Labs to index and "understand" travel videos, extracting specific landmarks directly from visual content.

**The Interface:** A polished React + TypeScript frontend styled with Tailwind CSS and shadcn/ui, featuring smooth Framer Motion animations to keep the user engaged during the complex data processing.

## Challenges we ran into
The "Impossible Route" Problem: Early versions suggested venues that were closed or required zig-zagging across a city. We solved this by implementing a deterministic TSP-like algorithm rather than relying on an LLM to "guess" a route.

Data Noise: Scraping 15+ sites results in a lot of "garbage" data. We had to build a robust filtering pipeline using blacklists and frequency ranking before passing data to Gemini.

Concurrency: Handling multiple heavy API calls and scraping tasks at once required a deep dive into Python’s asyncio and httpx to keep the response time under 2 minutes.

## Accomplishments that we're proud of
**Mathematical Precision:** We aren't just giving a list; we are giving a schedule that actually works based on real-world opening hours.

**Multimodal Integration:** Successfully building a pipeline that can extract a location from a video and turn it into a map coordinate.

**UI/UX:** Creating a "Puzzle Loader" and an interactive results page that feels like a premium consumer product, not just a hackathon project.

**Reservation System:** Automatically finding hotels with high ratings but great discounts with the best location in respect to the venues.

## What we learned
**LLMs are not Calculators:** We learned that while Gemini is incredible for "vibes" and validation, it cannot handle complex geospatial optimization. Separation of concerns between AI and deterministic algorithms is key.

**Geospatial Complexity:** Managing haversine distances and time-window constraints taught us the intricacies of logistics and urban routing.
