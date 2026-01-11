from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from twelvelabs.pipeline import analyze

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ENDPOINT 
# =========================
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