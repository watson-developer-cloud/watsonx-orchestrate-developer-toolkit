import os
import asyncio
from typing import List, Optional, Dict, Any
from enum import Enum
from fastapi import FastAPI, Header, Depends, HTTPException, Request
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
import logging
import traceback
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

from ibm_watsonx_ai import APIClient, Credentials
import time
import requests
import uuid

from ibm_watsonx_ai import APIClient
from langchain_ibm import ChatWatsonx
from langgraph.prebuilt import create_react_agent

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', None)
WATSONX_SPACE_ID = os.getenv('WATSONX_SPACE_ID', None)
WATSONX_API_KEY = os.getenv('WATSONX_API_KEY', None)
WATSONX_URL = os.getenv('WATSONX_URL','https://us-south.ml.cloud.ibm.com')
IS_WXO_AGENT = True

def get_access_token():
    file_suffix = "ga"
    api_key = WATSONX_API_KEY  
    file_path = './current_token' + file_suffix +'.txt'
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'accept': 'application/json'}
    data = {'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': api_key}

    if os.path.isfile(file_path):
        file_time = os.path.getmtime(file_path)
        if time.time() - file_time < 3600:
            print("Retrieved cached token for " + file_suffix)
            with open(file_path, "r") as file:
                return file.read()

    response = requests.post(url, headers=headers, data=data) 

    if response.status_code == 200:
        token_data = json.loads(response.text)
        token = token_data["access_token"]

        with open(file_path, "w") as file:
            file.write(token)
        print("Retrieved new token for " + file_suffix)
        return token
    else:
        raise Exception("Failed to get access token")



@tool
def web_search_duckduckgo(search_phrase: str):
    """Search the web using duckduckgo."""
    search = DuckDuckGoSearchResults()
    results = search.run(search_phrase) 
    return results

@tool
def news_search_duckduckgo(search_phrase: str):
    """Search news using duckduckgo."""
    search = DuckDuckGoSearchResults(backend="news")
    results = search.run(search_phrase) 
    return results


tool_choices = {
    "web_search_duckduckgo": web_search_duckduckgo,
    "news_search_duckduckgo": news_search_duckduckgo,
}


class ModelName(str, Enum):
    mistral_large = "mistralai/mistral-large"
    llama_3_1_405b = "meta-llama/llama-3-405b-instruct"
    llama_3_1_70b = "meta-llama/llama-3-1-70b-instruct"
    gpt_4_o_mini = "gpt-4o-mini"

DEFAULT_MODEL=ModelName.mistral_large

class ToolName(str, Enum):
    web_search_duckduckgo = "web_search_duckduckgo"
    news_search_duckduckgo = "news_search_duckduckgo"


class Function(BaseModel):
    arguments: Dict[str, Any]  # Expect a dictionary instead of a JSON string
    name: str

class AIToolCall(BaseModel):
    id: str
    function: Function
    type: str    

class AIRESTMessage(BaseModel):
    role: str  # user/human, system/ai, tool (tool response)
    content: Optional[str] = None
    tool_calls: Optional[List[AIToolCall]] = None 
    name: Optional[str] = None 
    tool_call_id: Optional[str] = None  
    def to_clean_dict(self):
        return {k: v for k, v in self.dict().items() if v is not None}


# Request Models
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

# Response Models
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


app = FastAPI()

class PromptRequest(BaseModel):
    prompt: str


def init_openai(model: str, parm_overrides: dict = {}):
    defaults = {
        'temperature': 0,
        'streaming': False
    }
    defaults.update(parm_overrides)
    return ChatOpenAI(model=model, **defaults)


def convert_messages_to_langgraph_format(messages: List[Message]) -> List[BaseMessage]:
    conv_messages = []
    max_message_length = 50000
    for msg in messages:
        if msg.content and len(msg.content) > max_message_length:
            msg.content = msg.content[:max_message_length]
        role = msg.role
        logger.info(f"Converting input message of type {role}")
        if role.lower() == 'user' or role.lower() == 'human':
            new_message = HumanMessage(content=msg.content)
        if role.lower() == 'system' :
            new_message = SystemMessage(content=msg.content) #Note some LLMs require this to be first message
            #new_message = AIMessage(content=msg.content)
        if role.lower() == 'assistant':
            content = ''
            additional_kwargs = {}
            if msg.content:
                content = msg.content
            new_message=AIMessage(content=content, additional_kwargs=additional_kwargs)
        if role.lower() == 'tool':
            tool_call_id = msg.tool_call_id
            content = None
            if msg.content:
                content = msg.content
            name = None
            if msg.name:
                name = msg.name
            new_message = ToolMessage(content=content, name=name, tool_call_id=tool_call_id)
        
        if new_message:
            conv_messages.append(new_message)
        
    return {
        "messages": conv_messages
    }   


# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


async def get_api_key(api_key_header: str = Depends(api_key_header)) -> Optional[str]:
    return api_key_header

async def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> Optional[str]:
    return credentials.credentials if credentials else None

async def get_current_user(
    api_key: Optional[str] = Depends(get_api_key),
    token: Optional[str] = Depends(get_bearer_token)
) -> Dict[str, Any]:
    return {"api_key": api_key, "token": token}


def convert_response_to_messages(response: dict) -> List[Message]:
    messages = []
    
    for msg in response['messages']:
        # Determine the role of the message based on its type or presence of attributes
        role = 'not found'
        if msg.type:
            role = msg.type
        logger.info(f"Processing role {role}")
        
        tool_calls = None
        
        if 'tool_calls' in msg:
            tool_calls = msg['tool_calls'] #<== never happens
            
        if msg.additional_kwargs:
            additional_kwargs = msg.additional_kwargs
            if 'tool_calls' in additional_kwargs:
                tool_calls = []
                for tool_call_data in additional_kwargs['tool_calls']:
                    # Parse the arguments JSON string into a dictionary
                    function_arguments = tool_call_data['function']['arguments'] #arguments are actual stringified json, may not want to loads them
                    if isinstance(function_arguments, str):
                        function_arguments = json.loads(function_arguments)

                    tool_call = AIToolCall(
                        id=tool_call_data['id'],
                        function=Function(
                            arguments=function_arguments,
                            name=tool_call_data['function']['name']
                        ),
                        type=tool_call_data['type']
                    )
                    tool_calls.append(tool_call)

        content = ""
        if msg.content:
            content = msg.content 
        
        id = None
        if msg.id:
            id = msg.id 
            
        name = None
        if 'name' in msg:
            name = msg['name']
        if msg.name:
            name = msg.name
            
        tool_call_id = None
        if 'tool_call_id' in msg:
            tool_call_id = msg['tool_call_id'] 
        if role == 'tool' and msg.tool_call_id:
            tool_call_id = msg.tool_call_id

        if role == 'human':
            message = Message(
            role='user',
            content=content
            )
        elif role == 'ai':
            message = Message(
            role='assistant',
            content=content
            )
        else:

            message = Message(
                role=role,
                content=content,
                tool_calls=tool_calls,
                name=name,
                tool_call_id=tool_call_id
            )
        messages.append(message)
    
    return messages

def get_llm_sync(messages: List[Message], model: str, thread_id: str, tools):
    logger.info(f"LLM Synchronous call using model {model} and tools {tools}")
    model_instance = None

    if 'gpt' in model:
        if not OPENAI_API_KEY:
            return "API key not set\n"
        model_instance = init_openai(model, {})
    else:
        client_model_instance = APIClient(credentials=Credentials(url=WATSONX_URL, token=get_access_token()),
                       space_id=WATSONX_SPACE_ID)
        model_instance = ChatWatsonx(model_id=model, watsonx_client=client_model_instance)

    logger.info(f"Starting with input messages: {messages}")
    inputs = convert_messages_to_langgraph_format(messages)
    logger.info(f"Calling langgraph with input: {inputs}")
    if tools:
       graph = create_react_agent(model_instance, tools=tools)  #Use state_modifier to add system prompt 
       response = graph.invoke(inputs)
    else:
        graph = model_instance
        response = graph.invoke(inputs['messages'])
    logger.info(f"Response: {response}")
    
    if hasattr(response, 'content'):
        results = response.content
        message = Message(
                role='ai',
                content=results,
                tool_calls=None,
                name=None,
                tool_call_id=None
            )
        response_messages = [message.to_clean_dict()]
    else:
        results = response["messages"][-1].content
        
    return results


def format_resp(struct):
    return "data: " + json.dumps(struct) + "\n\n"

async def get_llm_stream(messages: List[Message], model: str, thread_id: str, tools):
    if tools:
        use_tools = True
    else:
        use_tools = False
    logger.info(f"LLM Stream with tools {tools}")
    model_init_overrides = {'temperature': 0, 'streaming': True}
    if not thread_id:
        logger.warn("Warning no thread_id specified in input")
        thread_id = ""

    if 'gpt' in model:
        if not OPENAI_API_KEY:
            yield "API key not set\n"
        model_instance = init_openai(model, model_init_overrides)
    else:
        client_model_instance = APIClient(credentials=Credentials(url=WATSONX_URL, token=get_access_token()),
                       space_id=WATSONX_SPACE_ID)
        model_instance = ChatWatsonx(model_id=model, watsonx_client=client_model_instance)
        
    
    if use_tools:
        graph = create_react_agent(model_instance, tools=tools)
    else:
        graph = create_react_agent(model_instance, tools=[])
    
    inputs = ""
    try:
        inputs = convert_messages_to_langgraph_format(messages)

        show_stream_results_to_user = True
        search_message_displayed = False
        show_debug_messages = False
        async for event in graph.astream_events(inputs, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    if isinstance(content, str):
                        print(content, end="|")
                        if show_stream_results_to_user or show_debug_messages:
                            current_timestamp = str(int(time.time()))
                            struct = {
                                "id": str(uuid.uuid4()),
                                "object": "thread.message.delta",
                                "thread_id": thread_id,
                                "model": model,
                                "choices": [
                                    {
                                        "delta": {
                                            "content": content,
                                            "role": "assistant",
                                        }
                                    }
                                ],
                            }
                            event_content = format_resp(struct)
                            logger.info("Sending event content: " + event_content)
                            yield event_content
                            
                    if isinstance(content, List): 
                        for item in content:
                            if 'type' in item:
                                if item['type'] == 'text':
                                    yield item['text']
                                elif item['type'] == 'tool_use':
                                    print("tool_use")
                                    print(f"{str(item)}")
                                else:
                                    print("Received item of type " + item['type'])
                                    
            elif kind == "on_tool_start":
                logger.debug("--")
                printmsg =  f"Starting tool: {event['name']} with inputs: {event['data'].get('input')}"
                if not search_message_displayed:
                    usermsg = "I am thinking for a second...\n"
                    #yield usermsg 
                logger.debug("Stopping streaming to user while tool runs")
                show_stream_results_to_user = False
                search_message_displayed = True
                logger.info(printmsg)
            elif kind == "on_tool_end": 
                logger.debug(f"Done tool: {event['name']}")
                logger.debug(f"Tool output was: {event['data'].get('output')}")
                logger.debug("--")
                show_stream_results_to_user = True
                yield "\n"
            else:
                print("Received new event type: " + kind)
        yield ""
    except Exception as e:
        
        print(f"Exception {str(e)}")
        traceback.print_exc()
        print(f"Exception was with inputs {str(inputs)}")
        yield f"Error: {str(e)}\n"


@app.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    X_IBM_THREAD_ID: Optional[str] = Header(None, alias="X-IBM-THREAD-ID", description="Optional header to specify the thread ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info(f"Received POST /chat/completions ChatCompletionRequest: {request.json()}")

    thread_id = ''
    if  X_IBM_THREAD_ID:
        thread_id =  X_IBM_THREAD_ID
    if request.extra_body and request.extra_body.thread_id:
        thread_id = request.extra_body.thread_id
    logger.info("thread_id: " + thread_id)

    model = DEFAULT_MODEL
    if request.model:
        model = request.model
    selected_tools = [web_search_duckduckgo, news_search_duckduckgo]
    if request.stream:
        return StreamingResponse(get_llm_stream(request.messages, model, thread_id, selected_tools), media_type="text/event-stream")
    else:
        last_message, all_messages = get_llm_sync(request.messages, model, thread_id, selected_tools)
        id = str(uuid.uuid4())
        response = ChatCompletionResponse(
            id=id,
            object="chat.completion",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    index=0,
                    message=MessageResponse(
                        role="assistant",
                        content=last_message
                    ),
                    finish_reason="stop"
                )
            ]
        )
        return JSONResponse(content=response.dict())


@app.post("/chat/completions/stream")
async def chat_completions(
    request: ChatCompletionRequest,
    X_IBM_THREAD_ID: Optional[str] = Header(None, alias="X-IBM-THREAD-ID", description="Optional header to specify the thread ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info(f"Received POST /chat/completions/stream ChatCompletionRequest: {request.json()}")
    model = DEFAULT_MODEL
    if request.model:
        model = request.model

    thread_id = ''
    if  X_IBM_THREAD_ID:
        thread_id =  X_IBM_THREAD_ID
    if request.extra_body and request.extra_body.thread_id:
        thread_id = request.extra_body.thread_id

    logger.info("thread_id: " + thread_id)

    logger.info(
        f"/chat/completions/stream received with inputs:\n"
        f"Model: {model}\n"
        f"Context: {request.context}\n"
        f"Messages: {request.messages}\n"
        f"Stream: {request.stream}\n"
        f"Extra Body: {request.extra_body}\n"
        f"Thread ID: {thread_id}\n"
        f"Current User: {current_user}"
    )

    selected_tools = [web_search_duckduckgo, news_search_duckduckgo]
    return StreamingResponse(get_llm_stream(request.messages, model, thread_id, selected_tools), media_type="text/event-stream")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)