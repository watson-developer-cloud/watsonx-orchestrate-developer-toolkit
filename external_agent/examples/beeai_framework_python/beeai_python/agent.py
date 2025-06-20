import time
import uuid
from typing import AsyncIterable, Any

from beeai_framework.agents.experimental import RequirementAgent
from beeai_framework.agents.experimental.requirements.conditional import (
    ConditionalRequirement,
)
from beeai_framework.agents.experimental.utils._tool import (
    FinalAnswerTool,
    FinalAnswerToolSchema,
)
from beeai_framework.backend import ChatModelNewTokenEvent, ChatModel
from beeai_framework.emitter import EventMeta, EmitterOptions
from beeai_framework.memory import BaseMemory
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import ToolSuccessEvent, Tool, ToolStartEvent
from beeai_framework.tools.think import ThinkTool, ThinkSchema
from pydantic import BaseModel
from sse_starlette import ServerSentEvent

from beeai_python.models import ChatCompletionResponse, Choice, MessageResponse
from beeai_python.settings import AppSettings
from beeai_python.tools import search_web_tool
from beeai_python.utils import EmitFn, create_sse_emitter


class WxoBeeAgent:
    def __init__(self, agent: RequirementAgent, *, thread_id: str):
        self.agent = agent
        self._thread_id = thread_id

    @property
    def model_id(self) -> str:
        return self.agent._llm.model_id

    @staticmethod
    async def create(
        *, thread_id: str, llm: ChatModel, memory: BaseMemory
    ) -> "WxoBeeAgent":
        agent = RequirementAgent(
            llm=llm,
            memory=memory,
            tools=[ThinkTool(), search_web_tool],
            role="a deep researcher",
            instructions=[
                "Your task is to conduct in-depth research on the given topic.",
                "Before you start, thoroughly prepare a step-by-step plan for how you will solve the task.",
                "After each action, reflect on what you have obtained and what you need to do to gather evidence for the final answer."
            ],
            middlewares=[
                GlobalTrajectoryMiddleware(
                    included=[Tool], enabled=AppSettings.log_intermediate_steps
                )
            ],
            requirements=[
                ConditionalRequirement(ThinkTool, consecutive_allowed=False),
                ConditionalRequirement(
                    ThinkTool, force_at_step=1, force_after=[search_web_tool]
                ),
            ],
        )
        return WxoBeeAgent(agent=agent, thread_id=thread_id)

    async def run(self) -> ChatCompletionResponse:
        response = await self.agent.run(prompt=None)

        return ChatCompletionResponse(
            id=str(uuid.uuid4()),
            object="thread.message.delta",
            created=int(time.time()),
            model=self.model_id,
            choices=[
                Choice(
                    index=0,
                    message=MessageResponse(
                        role="assistant", content=response.answer.text
                    ),
                    finish_reason="stop",  # TODO
                )
            ],
        )

    def stream(self) -> AsyncIterable[ServerSentEvent]:
        def _create_tool_event(content: Any, meta: EventMeta) -> ServerSentEvent:
            data = {
                "id": meta.id or str(uuid.uuid4()),
                "object": "thread.run.step.delta",
                "thread_id": self._thread_id,
                "model": self.model_id,
                "created": int(meta.created_at.timestamp()),
                "choices": [{"delta": {"role": "assistant", "step_details": content}}],
            }
            return ServerSentEvent(data=data, id=data["id"], event=data["object"])

        def _create_message_event(details: Any, meta: EventMeta) -> ServerSentEvent:
            data = {
                "id": meta.id or str(uuid.uuid4()),
                "object": "thread.message.delta",
                "thread_id": self._thread_id,
                "model": self.model_id,
                "created": int(meta.created_at.timestamp()),
                "choices": [{"delta": {"role": "assistant", "content": details}}],
            }
            return ServerSentEvent(data=data, id=data["id"], event=data["object"])

        async def handler(emit: EmitFn) -> None:
            async def on_chat_model_stream(
                data: ChatModelNewTokenEvent, meta: EventMeta
            ) -> None:
                await emit(_create_message_event(data.value.get_text_content(), meta))

            async def on_tool_success(data: ToolSuccessEvent, meta: EventMeta) -> None:
                assert meta.trace, "ToolSuccessEvent must have trace"
                assert isinstance(meta.creator, Tool)

                await emit(
                    _create_tool_event(
                        {
                            "type": "tool_response",
                            "name": meta.creator.name,
                            "tool_call_id": meta.trace.run_id,
                            "content": data.output.get_text_content(),
                        },
                        meta,
                    )
                )

                # special case
                if isinstance(meta.creator, FinalAnswerTool):
                    await emit(
                        _create_message_event(
                            data.input.response
                            if isinstance(data.input, FinalAnswerToolSchema)
                            else data.input.model_dump_json(indent=2),
                            meta,
                        )
                    )

            async def on_tool_start(data: ToolStartEvent, meta: EventMeta) -> None:
                assert meta.trace, "ToolStartEvent must have trace"
                assert isinstance(meta.creator, Tool)

                if isinstance(meta.creator, FinalAnswerTool):
                    return

                await emit(
                    _create_tool_event(
                        {
                            "type": "tool_calls",
                            "tool_calls": [
                                {
                                    "id": meta.trace.run_id,
                                    "name": meta.creator.name,
                                    "args": data.input.model_dump()
                                    if isinstance(data.input, BaseModel)
                                    else data.input,
                                }
                            ],
                        },
                        meta,
                    )
                )
                if isinstance(meta.creator, ThinkTool):
                    await emit(
                        _create_tool_event(
                            {
                                "type": "thinking",
                                "content": f"{data.input.thoughts}\n\nNext Steps:\n"
                                + (
                                    "\n- ".join(data.input.next_step)
                                    if isinstance(data.input, ThinkSchema)
                                    else data.input.model_dump_json(indent=2)
                                ),
                            },
                            meta,
                        )
                    )

            await (
                self.agent.run(prompt=None)
                .on(
                    lambda event: isinstance(event.creator, Tool)
                    and event.name == "start",
                    on_tool_start,
                    EmitterOptions(match_nested=True),
                )
                .on(
                    lambda event: isinstance(event.creator, Tool)
                    and event.name == "success",
                    on_tool_success,
                    EmitterOptions(match_nested=True),
                )
                .on(
                    lambda event: isinstance(event.creator, ChatModel)
                    and event.name == "new_token",
                    on_chat_model_stream,
                    EmitterOptions(match_nested=True),
                )
            )

        return create_sse_emitter(handler)
