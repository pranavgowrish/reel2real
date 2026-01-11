from fastapi import FastAPI, Request
from google import genai
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import scrape_test
from ddgs import DDGS
import json
import itinerary_generator


from twelvelabs.pipeline import analyze

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from dotenv import load_dotenv
load_dotenv()

# =========================
# ENDPOINT 
# =========================
client = genai.Client(api_key="AIzaSyB5_Y46cWjFDep50FbvZyF5RMhciGLBTG4")



@app.post("/example")
async def example(request: Request):
    body = await request.json()

    chapter = body.get("chapter")
    question = body.get("question")

    print("Received chapter:", chapter, "question:", question)

    message = {
        "message": "Success"
    }

    return JSONResponse(content=message)


# =========================
# ENDPOINT: VIDEO ANALYSIS
# =========================
@app.post("/analyze-videos")
async def analyze_videos(request: Request):
    """
    Expected JSON body:
    {
        "video_urls": ["https://youtube.com/...", "https://instagram.com/reel/..."],
        "prompt": "Identify locations or places shown in the video"
    }
    """
    try:
        body = await request.json()

        video_urls = body.get("video_urls")
        prompt = body.get("prompt")

        if not video_urls or not isinstance(video_urls, list):
            return JSONResponse(
                status_code=400,
                content={"error": "video_urls must be a non-empty list"}
            )

        if not prompt or not isinstance(prompt, str):
            return JSONResponse(
                status_code=400,
                content={"error": "prompt must be a string"}
            )

        results = analyze(video_urls, prompt)

        return JSONResponse(
            content={
                "status": "success",
                "results": results
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
    
    return JSONResponse(content=message)

@app.post("/example")
async def example(request: Request):
    body = await request.json()  # <-- parse JSON body

    chapter = body.get("chapter")
    question = body.get("question") 

    print("Received chapter:", chapter, "question:", question)
        
    message = {
        "message": "Success"
    }
    
    return JSONResponse(content=message)



@app.post("/confirm")
async def gemini_confirm(request: Request):
    body = await request.json()
    city = body.get("city")
    vibe = body.get("vibe")
    budget = body.get("budget")

    print("Received city:", city, "vibe:", vibe, "budget:", budget)

    top_places = await scrape_test.collect_venues(city, vibe)

    prompt = f"""Your goal is to confirm if the following list of venues are best in the location {city} for a vacationer seeking an {vibe} vibe within a budget of {budget}.
    Top Places: {top_places}
    Only include places that are truly the best for the given vibe and give me only a max of 6 places. ONLY IF NEEDED IF THERE IS NOT ENOUGH GOOD PLACES IN THE LIST, you can add up to 4 additional places that fit the vibe really well and near the other places. Add tags to a max of 3 of these locations like "Most Popular", "Hidden Gem", "Scenic", etc. MAKE SURE TO Respond in a dict format: {{"confirmed_places": [{{"name": "Exact Google Maps Place Name", "desc": "1 line short description", "tag": "Most Popular"  (Optional - only on max 3 places)}}]}}.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        print("Gemini response:", response)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```
        response_text = response_text.strip()

        response_data = json.loads(response_text)
        confirmed_places = []
        for place in response_data.get("confirmed_places", []):
            place_name = place.get("name")
            image_url = get_image_url(f"{place_name} {city}")
            
            confirmed_place = {
                "name": place_name,
                "image": image_url
            }
            
            # Add tag if it exists
            if "tag" in place:
                confirmed_place["tag"] = place["tag"]
            
            if "desc" in place:
                confirmed_place["desc"] = place["desc"]
            
            confirmed_places.append(confirmed_place)
        
        message = {
            "result": json.dumps({"confirmed_places": confirmed_places})
        }
        print(message)
        return JSONResponse(content=message)
    
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return JSONResponse(
            content={"error": f"Failed to parse API response: {str(e)}"},
            status_code=400
        )
    except Exception as e:
        print(f"Error in /confirm endpoint: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={"error": f"Server error: {str(e)}"},
            status_code=500
        )


def get_image_url(poi):
    with DDGS() as ddgs:
        for r in ddgs.images(poi, max_results=1):
            return r["image"]
    return None


@app.post("/itin")
async def itin(request: Request):
    body = await request.json() 

    places = body.get("places")
    city = body.get("city") 

    itinerary = await itinerary_generator.generate_itinerary(
        places,
        city=city,
        start_time_minutes=540,
        hotel_index=0
    )

    print("Generated itinerary:", itinerary)
        
    message = {
        "final": itinerary
    }
    
    return JSONResponse(content=message)
