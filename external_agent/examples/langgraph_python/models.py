from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Any

class ModelName(str, Enum):
    mistral_large = "mistralai/mistral-large"
    llama_3_1_405b = "meta-llama/llama-3-405b-instruct"
    llama_3_1_70b = "meta-llama/llama-3-1-70b-instruct"
    gpt_4_o_mini = "gpt-4o-mini"

class ToolName(str, Enum):
    web_search_duckduckgo = "web_search_duckduckgo"
    news_search_duckduckgo = "news_search_duckduckgo"

DEFAULT_MODEL=ModelName.mistral_large

class Function(BaseModel):
    arguments: Dict[str, Any]
    name: str

class AIToolCall(BaseModel):
    id: str
    function: Function
    type: str    

class AIRESTMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[AIToolCall]] = None 
    name: Optional[str] = None 
    tool_call_id: Optional[str] = None  
    def to_clean_dict(self):
        return {k: v for k, v in self.dict().items() if v is not None}

class Message(BaseModel):
    role: str = Field(..., description="The role of the message sender", pattern="^(user|assistant|system|tool)$")
    content: str = Field(..., description="The content of the message")

class ExtraBody(BaseModel):
    thread_id: Optional[str] = Field(None, description="The thread ID for tracking the request")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default_factory=lambda: DEFAULT_MODEL, description="ID of the model to use")
    context: Dict[str, Any] = Field({}, description="Contextual information for the request")
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    stream: Optional[bool] = Field(False, description="Whether to stream responses as server-sent events")
    extra_body: Optional[ExtraBody] = Field(None, description="Additional data or parameters")

class MessageResponse(BaseModel):
    role: str = Field(..., description="The role of the message sender", pattern="^(user|assistant)$")
    content: str = Field(..., description="The content of the message")

class Choice(BaseModel):
    index: int = Field(..., description="The index of the choice")
    message: MessageResponse = Field(..., description="The message")
    finish_reason: Optional[str] = Field(None, description="The reason the message generation finished")

class ChatCompletionResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field("chat.completion", description="The type of object returned, should be 'chat.completion'")
    created: int = Field(..., description="Timestamp of when the completion was created")
    model: str = Field(..., description="The model used for generating the completion")
    choices: List[Choice] = Field(..., description="List of completion choices")
