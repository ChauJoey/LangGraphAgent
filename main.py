from fastapi import FastAPI
from assistant import agent
from pydantic import BaseModel
import json

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    user_input: str

@app.post("/chat")
def chat(req: ChatRequest):
    # {"user_input": "where to dehire OOLU9933088 TEMU5943297"}
    result = agent.invoke({"user_input": req.user_input})
    return {"response": json.loads(result["final_return_depots"])}