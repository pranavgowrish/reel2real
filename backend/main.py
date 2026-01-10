from fastapi import FastAPI, Request
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

