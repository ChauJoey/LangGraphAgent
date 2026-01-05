import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from info_board.update_info import update_info
from assistant import agent
from pydantic import BaseModel
import json
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print("Starting background scheduler...")

    task = asyncio.create_task(information_board_scheduler())

    yield  # ⬅️ FastAPI 开始接收请求

    # shutdown
    print("Shutting down background scheduler...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def information_board_scheduler():
    while True:
        try:
            print("Updating information board...")
            update_info()
            print("Information board updated")
        except Exception as e:
            print("Update failed:", e)

        await asyncio.sleep(60 * 60)  # 30 分钟


app = FastAPI(lifespan=lifespan)

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