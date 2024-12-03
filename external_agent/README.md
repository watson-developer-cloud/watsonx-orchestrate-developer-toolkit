# IBM watsonx orchestrate - external agent support

For official feature documentation, refer to [link](https://developer.ibm.com/apis/catalog/watsonorchestrate--custom-assistants/api/API--watsonorchestrate--ibm-watsonx-orchestrate-api#Register_an_external_chat_completions_agent__agents_external_chat_post).

## Starter Guide to Using the External Agent Feature

### Create the Agent
Begin by creating an agent that exposes a chat streaming endpoint. Ensure the endpoint adheres to the specified standards and streams events correctly according to the [provided specifications](external_agent/spec.yaml).

### Implement Authentication
The agent must support authentication through either of the following methods:

1. Bearer Token Authentication
2. API Key Authentication using an `x-api-key` header.

### Deploy the Agent
Once the agent is ready, deploy it externally (e.g., using [code engine](https://www.ibm.com/products/code-engine)).

### Register the Agent
After deployment, register the agent according to the instructions provided in our product documentation.