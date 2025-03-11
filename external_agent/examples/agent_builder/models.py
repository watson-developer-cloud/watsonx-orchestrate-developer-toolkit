from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(
        ...,
        description="The role of the message sender",
        pattern="^(user|assistant|system|tool)$",
    )
    content: Optional[str] = Field(..., description="The content of the message")
    tool_calls: Optional[list] = None # for tool call msgs
    tool_call_id: Optional[str] = None # for tool resp msgs


class ExtraBody(BaseModel):
    thread_id: Optional[str] = Field(
        None, description="The thread ID for tracking the request"
    )


class ChatCompletionRequest(BaseModel):
    model: str = Field(default_factory=lambda: "", description="ID of the model to use")
    context: Dict[str, Any] = Field(
        {}, description="Contextual information for the request"
    )
    messages: List[Message] = Field(
        ..., description="List of messages in the conversation"
    )
    stream: Optional[bool] = Field(
        False, description="Whether to stream responses as server-sent events"
    )
    extra_body: Optional[ExtraBody] = Field(
        None, description="Additional data or parameters"
    )


class MessageResponse(BaseModel):
    role: str = Field(
        ..., description="The role of the message sender", pattern="^(user|assistant)$"
    )
    content: str = Field(..., description="The content of the message")


class Choice(BaseModel):
    index: int = Field(..., description="The index of the choice")
    message: MessageResponse = Field(..., description="The message")
    finish_reason: Optional[str] = Field(
        None, description="The reason the message generation finished"
    )


class ChatCompletionResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(
        "chat.completion",
        description="The type of object returned, should be 'chat.completion'",
    )
    created: int = Field(
        ..., description="Timestamp of when the completion was created"
    )
    model: str = Field(..., description="The model used for generating the completion")
    choices: List[Choice] = Field(..., description="List of completion choices")
