import logging
import warnings

from beeai_python.agent import WxoBeeAgent
from beeai_python.utils import create_llm, init_memory
from beeai_python.models import (
    ChatCompletionRequestBody,
)
from fastapi import FastAPI, HTTPException, Header
from sse_starlette import EventSourceResponse
from starlette import status
from starlette.responses import JSONResponse
from beeai_python.settings import AppSettings

warnings.filterwarnings("ignore")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

app = FastAPI()


@app.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequestBody,
    thread_id: str = Header("", alias="X-IBM-THREAD-ID"),
    api_key: str | None = Header(None, alias="X-API-Key"),
):
    if not thread_id and request.extra_body:
        thread_id = request.extra_body.thread_id or ""

    logger.info(f"Received request\n{request.model_dump_json()} (ID: {thread_id})")

    if api_key != AppSettings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key",
        )

    agent = await WxoBeeAgent.create(
        llm=create_llm(request.model, stream=request.stream),
        memory=await init_memory(request.messages),
        thread_id=thread_id,
    )
    if request.stream:
        stream = agent.stream()
        return EventSourceResponse(stream)
    else:
        content = await agent.run()
        return JSONResponse(content=content.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
