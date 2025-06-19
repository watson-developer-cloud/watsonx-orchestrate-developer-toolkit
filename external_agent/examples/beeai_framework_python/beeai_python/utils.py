import asyncio
import contextlib
import json
from asyncio import Queue
from typing import TypeVar, Awaitable, Any, Callable

from beeai_framework.adapters.watsonx import WatsonxChatModel
from beeai_framework.backend import AssistantMessage, ToolMessage, SystemMessage, ChatModel, Message
from beeai_framework.memory import BaseMemory, UnconstrainedMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.utils.strings import to_json
from sse_starlette import ServerSentEvent


from beeai_python.models import Message
from beeai_framework.backend.message import (
    Message as FrameworkMessage,
    UserMessage,
    AssistantMessageContent,
    MessageTextContent,
    MessageToolCallContent,
    MessageToolResultContent,
)

from beeai_python.settings import AppSettings


def wxo_message_to_beeai_message(message: Message) -> FrameworkMessage:
    match message.role:
        case "human":
            return UserMessage(message.content)
        case "user":
            return UserMessage(message.content)
        case "system":
            return SystemMessage(message.content)
        case "tool":
            return ToolMessage(
                MessageToolResultContent(
                    result=message.content,
                    tool_call_id=message.tool_call_id,
                    tool_name=message.tool_calls[0].function.name
                    if message.tool_calls
                    else "",
                )
            )
        case "assistant":
            parts: list[AssistantMessageContent] = []
            if message.content:
                parts.append(MessageTextContent(text=message.content))
            if message.tool_calls:
                parts.extend(
                    [
                        MessageToolCallContent(
                            id=p.id,
                            tool_name=p.function.name,
                            args=json.dumps(p.function.arguments),
                        )
                        for p in message.tool_calls
                    ]
                )
            return AssistantMessage(parts)
        case _:
            raise ValueError(f"Invalid role: {message.role}")


T = TypeVar("T")
EmitFn = Callable[[ServerSentEvent | Any], Awaitable[None]]


async def create_sse_emitter(
    handler: Callable[[EmitFn], Any],
):
    queue = Queue[ServerSentEvent | None]()

    async def emit(data: Any) -> Any:
        event = (
            ServerSentEvent(
                id=data.id,
                data=to_json(data.data, sort_keys=False, exclude_none=True),
                event=data.event,
                comment=data.comment,
                sep=data._sep,
                retry=data.retry,
            )
            if isinstance(data, ServerSentEvent)
            else ServerSentEvent(data=to_json(data, sort_keys=False, exclude_none=True))
        )
        await queue.put(event)

    async def wrapper() -> None:
        try:
            await handler(emit)
        finally:
            await queue.put(None)

    task = asyncio.create_task(wrapper())

    try:
        while True:
            try:
                item = await queue.get()
                if item is not None:
                    yield item
                queue.task_done()
                if item is None:
                    break
            except asyncio.CancelledError:
                task.cancel()
                raise
    finally:
        with contextlib.suppress(asyncio.CancelledError):
            await task


def create_llm(model_id: str, *, stream: bool | None = None) -> ChatModel:
    llm = WatsonxChatModel(
        model_id=model_id.removeprefix("watsonx/").lower(),
        api_key=AppSettings.watsonx_api_key,
        project_id=AppSettings.watsonx_project_id,
        base_url=AppSettings.watsonx_url,
        middlewares=[
            GlobalTrajectoryMiddleware(enabled=AppSettings.log_intermediate_steps)
        ],
    )
    llm.parameters.stream = bool(stream)
    return llm


async def init_memory(messages: list[Message]) -> BaseMemory:
    memory = UnconstrainedMemory()

    converted_messages = [wxo_message_to_beeai_message(msg) for msg in messages]
    for msg, next_msg, next_next_msg in zip(
        converted_messages,
        converted_messages[1:] + [None],
        converted_messages[2:] + [None, None],
    ):
        if isinstance(msg, SystemMessage):
            continue

        # Remove a handoff tool call
        if (
            next_next_msg is None  # last pair
            and isinstance(msg, AssistantMessage)
            and msg.get_tool_calls()
            and isinstance(next_msg, ToolMessage)
            and next_msg.get_tool_results()
            and msg.get_tool_calls()[0].id
            == next_msg.get_tool_results()[0].tool_call_id
            and msg.get_tool_calls()[0].tool_name.lower().startswith("transfer_to_")
        ):
            break

        await memory.add(msg)

    return memory
