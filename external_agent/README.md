# IBM watsonx orchestrate - external agent support

For official feature documentation, refer to [link](https://developer.ibm.com/apis/catalog/watsonorchestrate--custom-assistants/api/API--watsonorchestrate--ibm-watsonx-orchestrate-api#Register_an_external_chat_completions_agent__agents_external_chat_post).

## Starter Guide to Using the External Agent Feature

For examples, check out the [examples](examples).

### Create the Agent
Begin by creating an agent that exposes a chat streaming endpoint that emits the following events:


1. **Assistant response event**  

This event captures the agent response that will be shown to end user. For example:
```
data: {"id": "run-8c1182", "object": "thread.message.delta", "thread_id": "c91e2e38-7b42-43d7-b913-0273951350a9", "model": "agent-02", "created": 1728566547, "choices": [{"delta": {"role": "assistant", "content": "Here are the upcoming holidays in the US:\n\n- National Coming Out Day: October 11, 2024\n- Yom Kippur: October 12, 2024\n- Columbus Day: October 14, 2024\n- Sukkot: October 17, 2024\n- Sweetest Day: October 19, 2024\n- National Cat Day: October 29, 2024\n- Halloween: October 31, 2024\n- Diwali: November 01, 2024\n\nSource:\n- [Holidays Calendar](https://www.holidayscalendar.com/countries/united-states/)\n- [Time and Date](https://www.timeanddate.com/holidays/us/)\n- [Federal Holidays](https://www.federalholidays.net/usa/federal-holidays-2024.html)\n- [Dayspedia](https://dayspedia.com/us/calendar/holidays/)"}}]}
```


2. **Thinking step event**  

This event is optional. It's the intermediate thinking that an agent can produce. For example:
```
data: {"id": "step-d08460", "object": "thread.run.step.delta", "thread_id": "c91e2e38-7b42-43d7-b913-0273951350a9", "model": "agent-02/mistralai/mistral-large-latest", "created": 1728566531, "choices": [{"delta": {"role": "assistant", "step_details": {"type": "thinking", "content": "The agent's response is a generic greeting and does not address the user's specific question about upcoming holidays in the US. I should use the available tools to find the relevant information and provide a more specific and helpful response."}}]}
```


3. **Tool call event**  

This the event that captures an agent's tool calls. A single event can represent multiple tool calls. For example:
```
data: {"id": "step-a0844e", "object": "thread.run.step.delta", "thread_id": "c91e2e38-7b42-43d7-b913-0273951350a9", "model": "agent-02/mistralai/mistral-large-latest", "created": 1728566532, "choices": [{"delta": {"role": "assistant", "step_details": {"type": "tool_calls", "tool_calls": [{"name": "find_employee_by_name", "args": {"name": "vsingh"}, "id": "e32ff32a4"}]}}]}
```

Note: In the tool call array `"tool_calls": [{"name": "find_employee_by_name", "args": {"name": "vsingh"}, "id": "e32ff32a4"}]`, each tool_call can have a unique id like `e32ff32a4`.
This id is used to match with Tool response event.

4. **Tool response event**  

This the event that captures an agent's tool response output. Each event represents the output from a single tool call. For example:
```
data: {"id": "step-03050c", "object": "thread.run.step.delta", "thread_id": "ae1b353f-65b9-4668-b1e8-9298979c9697", "model": "agent-02", "created": 1729091694, "choices": [{"delta": {"role": "assistant", "step_details": {"type": "tool_response", "content": "[{'cellPhone': None, 'city': None, 'country': 'India', 'dateOfBirth': datetime.date(1998, 6, 30), 'defaultFullName': 'Vijaya Singh', 'department': 'HR Total Rewards (5000145)', 'email': 'kota.manaswini@partner.ibm.com', 'firstName': 'Vijaya', 'gender': ' ', 'hireDate': datetime.date(2023, 6, 30), 'lastName': 'Singh', 'salary': None, 'state': None, 'title': 'Digital Consultant', 'userId': '103451', 'businessPhone': None, 'location': 'Hyderabad (6200-0005)'}]", "name": "find_employee_by_name", "tool_call_id": "e32ff32a4"}}}]}
```


Note: In this example, the `event.choices[0].delta.step_details.tool_call_id` needs to match the corresponding `tool_calls[0].id` in `event.choices[0].delta.step_details.tool_calls[0].id`.
The `tool_call_id` of the `tool_response` being present and matching the `id` of the `tool_call` will be required for the Watsonx Orchestrate UX to render Chain of Thoughts correctly.


5. **End of a single call**  

At the end of the stream, emit the following:
```
data: [DONE]
```

For more details regarding input & output specifications, refer to the [provided specifications](spec.yaml).


### Implement Authentication
The agent must support authentication through either of the following methods:

1. Bearer Token Authentication
2. API Key Authentication using an `x-api-key` header.

### Deploy the Agent
Once the agent is ready, deploy it externally (e.g., using [code engine](https://www.ibm.com/products/code-engine)).

### Register the Agent
After deployment, register the agent according to the instructions provided in our product documentation.