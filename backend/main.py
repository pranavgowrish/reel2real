from fastapi import FastAPI, Request
from google import genai
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import scrape_test
from ddgs import DDGS
import json
import itinerary_generator
import re

import deeplinking

#from process_video import process_multiple_videos_from_urls
#from analyze_video import analyze_existing_video, analyze_multiple_videos

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
client = genai.Client(api_key="AIzaSyCipIj_9yjHcOLkx_nEIYnNdy1fVv-ymDc")



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
# ENDPOINT: VIDEO ANALYSIS (Full Pipeline - Download + Upload + Analyze)
# =========================
@app.post("/analyze-videos")
async def analyze_videos(request: Request):
    """
    Full pipeline: Download videos from URLs, upload to Twelve Labs, and analyze.
    
    Expected JSON body:
    {
        "video_urls": ["https://youtube.com/...", "https://instagram.com/reel/..."],
        "prompt": "Identify locations or places shown in the video"
    }
    
    Returns analysis results for each video.
    """
    try:
        print("Received /analyze-videos request")
        body = await request.json()

        video_urls = await scrape_test.extract_video_urls()
        prompt = body.get("prompt")

        # Validation
        if not video_urls or not isinstance(video_urls, list):
            return JSONResponse(
                status_code=400,
                content={"error": "video_urls must be a non-empty list"}
            )

        if len(video_urls) == 0:
            return JSONResponse(
                status_code=400,
                content={"error": "video_urls cannot be empty"}
            )

        if not prompt or not isinstance(prompt, str):
            return JSONResponse(
                status_code=400,
                content={"error": "prompt must be a string"}
            )

        # CHANGED: Use process_multiple_videos_from_urls from process_video.py
        # This handles: download → upload → index → analyze
        results = process_multiple_videos_from_urls(
            video_urls=video_urls,
            prompt=prompt,
            index_name=None,  # Auto-generate index name
            output_dir="videos",
            temperature=0.2,
            max_tokens=2000
        )

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


# =========================
# ENDPOINT: ANALYZE EXISTING VIDEOS (No Download/Upload)
# =========================
# @app.post("/analyze-existing-videos")
# async def analyze_existing_videos(request: Request):
#     """
#     Analyze videos that are already indexed in Twelve Labs.
#     Use this when you already have video_ids.
    
#     Expected JSON body:
#     {
#         "video_ids": ["video_id_1", "video_id_2"],
#         "prompt": "What products are shown in this video?"
#     }
#     """
#     try:
#         body = await request.json()

#         video_ids = body.get("video_ids")
#         prompt = body.get("prompt")

#         # Validation
#         if not video_ids or not isinstance(video_ids, list):
#             return JSONResponse(
#                 status_code=400,
#                 content={"error": "video_ids must be a non-empty list"}
#             )

#         if len(video_ids) == 0:
#             return JSONResponse(
#                 status_code=400,
#                 content={"error": "video_ids cannot be empty"}
#             )

#         if not prompt or not isinstance(prompt, str):
#             return JSONResponse(
#                 status_code=400,
#                 content={"error": "prompt must be a string"}
#             )

#         # Use analyze_multiple_videos from analyze_video.py
#         # This only does the analysis step (videos already indexed)
#         results = analyze_multiple_videos(
#             video_ids=video_ids,
#             prompt=prompt,
#             temperature=0.2,
#             max_tokens=2000
#         )

#         return JSONResponse(
#             content={
#                 "status": "success",
#                 "results": results
#             }
#         )

#     except Exception as e:
#         return JSONResponse(
#             status_code=500,
#             content={"error": str(e)}
#         )

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
    #top_places = ["Central Park", "Statue of Liberty", "Times Square", "Brooklyn Bridge", "Metropolitan Museum of Art"]

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
        
        # Extract JSON from markdown code blocks or extra text
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            # Found JSON in markdown code block
            response_text = json_match.group(1).strip()
        else:
            # Try to find raw JSON object (in case there's extra text)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0).strip()
            # If no match, proceed with cleaned response_text as before

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
        print(f"Response text was: {response_text}")
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
    )

    print("Generated itinerary:", itinerary)
        
    message = {
        "final": itinerary
    }
    
    return JSONResponse(content=message)

@app.post("/hotel")
async def hotel(request: Request):
    body = await request.json() 

    address = body.get("address")
    checkin = body.get("checkin")
    checkout = body.get("checkout")
    adults = body.get("adults")

    list= await deeplinking.run(
        address=address,
        checkin=checkin,
        checkout=checkout,
        adults=adults
    )
    print("Generated hotel link:", list[0])
    message = {
        "name":  list[1],
        "link": list[0],
        "address": list[2]
    }
    
    return JSONResponse(content=message)

@app.get("/")
def wake_up():
    return {"status": "backready"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
