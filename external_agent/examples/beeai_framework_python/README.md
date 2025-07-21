# IBM Watsonx Orchestrate - External Agent Example (BeeAI Framework)

Use these examples to kick-start your external agent development.

For official feature documentation, refer to the [IBM Developer API Catalog](https://developer.ibm.com/apis/catalog/watsonorchestrate--custom-assistants/api/API--watsonorchestrate--ibm-watsonx-orchestrate-api#Register_an_external_chat_completions_agent__agents_external_chat_post).

## Overview

The application uses built-in support for the Watsonx Orchestrate in the [BeeAI Framework](https://framework.beeai.dev/integrations/watsonx-orchestrate).
Internally the script uses [RequirementAgent](https://framework.beeai.dev/experimental/requirement-agent) with Tavily Search tool (see `wxo_beeai/agent.py`).

## Deployment Instructions

### Step 1: Create a Code Engine Project

1. **Using IBM Cloud Web UI:**
   - Navigate to [IBM Cloud Code Engine Projects](https://cloud.ibm.com/containers/serverless/projects) and select **Create**. Name your project, for instance `wxo-agent-test1`.
   - Select the agent you created (`wxo-agent-test1`) and choose the **Application** menu item from the left navigation panel.

2. **Create an API Key for Registry Secret:**
   - Select **Manage** from the title bar menu and go to **Access (IAM)**.
   - From the left navigation menu, select **API keys**.
   - Click **Create** and copy the new API key for use in the registry secret.

3. **Create the Code Engine Application:**
   - Click the **Create** button to start creating an application.
   - Under **Code**, select **Build container image from source code**.
   - In the **Code repo URL** field, enter `https://github.com/watson-developer-cloud/watsonx-orchestrate-developer-toolkit`.
   - Click **Specify build details**:
     - **SSH secret:** None
     - **Branch name:** main
     - **Context directory:** `external_agent/examples/beeai_python`
     - Click **Next**
     - **Dockerfile:** Dockerfile (leave default)
     - Click **Next**
     - Under **Registry secret**, create a secret (if one doesn't exist) using the **API Key** created above
   - **Application name:** Any name, for instance `wxo-agent-test1-app1`
   - **Domain mappings:** Public

4. **Set Environment Variables:**
   - Add the following environment variables (see `.env.example`)
     - `WATSONX_URL`
     - `WATSONX_REGION`
     - `WATSONX_PROJECT_ID`
     - `WATSONX_API_KEY`
     - `API_KEY`
     - `TAVILY_API_KEY` (if needed)
   - Select the `Create` button

5. **Test the Application:**
   - Choose **Test application** and click **Application URL**.
     - It is expected this page will not be found, we need to slightly update the path
   - Append `/docs` to the end of the URL path to view a formatted API page.
     - Example: `https://wxo-agent-test1-app1.1pj4w3r1pi47.us-south.codeengine.appdomain.cloud/docs`

### Step 2: Register the New Endpoint as an External Agent

1. **In IBM watsonx orchestrate Web UI:**
   - From the top left hamburger menu, select **Agent Configuration**.
   - Select **Assistants** from the left-hand navigation.
   - Click the **Add assistant** button on the top right.
   - Choose **External Assistant** at the top of the dialog.
   - Check the **External-agent Assistant** box.

2. **Enter Details:**
   - **Display Name:** e.g., News Today
   - **Description:** Enter a description of capabilities, for instance `Agent to retieve current news`
   - **API Key:** Enter your API key.
   - **Service Instance URL:** Use the Test URL with `/chat/completions` appended.
     - Example: `https://wxo-agent-test1-app1.1pj4w3r1pi47.us-south.codeengine.appdomain.cloud/chat/completions`

### Step 3: Call the new External Agent from Orchestrate

1. **In IBM watsonx orchestrate Web UI:**
   - From the top left hamburger menu, select **Agent Configuration**.
   - Select **Chat** from the left-hand navigation.
   - Type a question that should route to the new agent, like `Can you tell me news about the Nasdaq today?`
   - The results from the external agent should be streamed to the IBM watsonx Orchestrate chat window