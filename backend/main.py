from fastapi import FastAPI, Request
from google import genai
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key="AIzaSyBYfWImgEp82cQsXTRaRdZ5lzQ85wldnas")



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

    


    prompt = f"""You are a teaching assistant for college-level students learning C++. Here is their code and the error they are encountering:
    Code: {code}
    Error: {error}
    Don't give the answer directly. Instead, briefly guide them through the problem with hints and questions to help them understand and solve it on their own. Keep it short and sweet. use markdown to be clear
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=prompt
    )
    message = {
        "hint": response.text
    }
    return JSONResponse(content=message)
    return await gemini.ask_merlin(payload)

