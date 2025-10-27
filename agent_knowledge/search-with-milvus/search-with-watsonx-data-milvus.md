# Using Milvus in watsonx.data as an Agent Knowledge Repository for Cloud Pak for Data

This guide explains how to configure watsonx.data Milvus as a content repository for Agent Knowledge in watsonx Orchestrate **on Cloud Pak for Data**, using embedding models from watsonx.ai Cloud Pak for Data.

## Prerequisites

Before starting this integration, ensure you have:

- **Cloud Pak for Data environment**: A properly configured Cloud Pak for Data environment
- **watsonx.data instance**: A properly configured watsonx.data instance on Cloud Pak for Data
  - For installation instructions, see [Installing and administering Cloud Pak for Data](https://www.ibm.com/docs/en/cloud-paks/cp-data/5.2.x?topic=installing-administering-cloud-pak-data)
- **Milvus service**: Added to your watsonx.data console
  - For setup instructions, see [Adding a Milvus service](https://www.ibm.com/docs/en/watsonxdata/standard/2.2.x?topic=milvus-adding-service)
- **Access credentials**: Administrative access to both watsonx.data and watsonx.ai
- **Documents**: Content you want to make available to your agents

## Table of Contents

- [Step 1: Collect Milvus Connection Information](#step-1-collect-milvus-connection-information)
- [Step 2: Ingest Data into Milvus](#step-2-ingest-data-into-milvus)
- [Step 3: Connect to Agent Knowledge in watsonx Orchestrate](#step-3-connect-to-agent-knowledge-in-watsonx-orchestrate)
- [Troubleshooting](#troubleshooting)
- [Conclusion](#conclusion)

## Integration Process

### Step 1: Collect Milvus Connection Information

#### Authentication Credentials

- **Username**: Default is `cpadmin` for Milvus service on watsonx.data
  - You can verify this in the Milvus "Access control" panel in the Infrastructure Manager
- **Password**: Use the password created for the Milvus service user

#### Connection Details

1. Navigate to the **Infrastructure manager** page
2. Select your Milvus service to open the **Details** page
3. Click **View connect details**
4. Record the following information:
   - GRPC host
   - GRPC port
   - SSL certificate

### Step 2: Ingest Data into Milvus

Choose one of the following methods to populate your Milvus vector database:

#### Option 1: Using watsonx.ai Interface

1. **Create a Milvus connection**:
   - Go to watsonx.ai Project Assets page
   - Click **New asset** > **Connect a data source** > **Milvus** > **Next**
   - Enter your connection details and credentials
   - Click **Test connection** > **Create**

   ![Milvus Connection Setup](./assets/create-milvus-connection.png)

2. **Create a vector index and upload documents**:
   - On the watsonx.ai Project Assets page, click **New asset** > **Ground gen AI with vectorized documents**
   - Select **watsonx.data Milvus** as the vector store
   - Fill in name and description
   - Select your Milvus connection
   - Choose your **Database** and **Embeddings model** > click **Next**

   ![Milvus Index Creation](./assets/create-milvus-index-watsonx-ai.png)

3. **Create a collection and upload documents**:
   - Click **New collection**
   - Enter a unique collection name
   - Select files to include
   - Click **Create**
   - Note the values for **Document name** and **Text** under Advanced settings (needed for Agent Knowledge setup)

   ![Milvus Collection Creation](./assets/create-milvus-collection-and-ingest-watsonx-ai.png)

> **Important**: By default, `document_name` and `text` are the two main fields created in the Milvus collection schema. When searching this collection using custom code, you must specify these as `output_fields`. When configuring Agent Knowledge, map these to the `Title` and `Body` fields.

#### Option 2: Using Custom Code

To programmatically ingest documents:

1. **Install dependencies**:
   ```bash
   python3 -m pip install pymilvus langchain langchain-milvus langchain-ibm ibm-watsonx-ai PyPDF2
   ```

2. **Set environment variables**:
   ```bash
   export MILVUS_HOST="Your Milvus GRPC host"
   export MILVUS_PORT="Your Milvus GRPC port"
   export MILVUS_USER="cpadmin"  # Default username for watsonx.data Milvus on-prem
   export MILVUS_PASSWORD="Your on-prem watsonx.data Milvus password"
   export MILVUS_PEM_PATH="path/to/milvus/tls/certificate"
   export MILVUS_COLLECTION_NAME="your_collection_name"

   export WATSONX_AI_URL="Your on-prem watsonx.ai URL"
   export WATSONX_AI_USERNAME="Your on-prem watsonx.ai username"
   export WATSONX_AI_PASSWORD="Your on-prem watsonx.ai password"
   export WATSONX_AI_PROJECT_ID="Your on-prem watsonx.ai project ID"
   ```

3. **Modify and run the sample script**:
   - Update `SOURCE_FILES`, `SOURCE_URLS`, and `SOURCE_TITLES` in the script
   - Run the script:
     ```bash
     python3 index-with-milvus.py
     ```

### Step 3: Connect to Agent Knowledge in watsonx Orchestrate

> **Important**: The embedding model used for search must match the one used during data ingestion in Step 2.

To configure watsonx.data Milvus as a content repository in watsonx Orchestrate:

1. Navigate to the Agent Knowledge section in watsonx Orchestrate
2. Follow the integration steps for Milvus content repository
3. Configure the connection using the details collected in Step 1
4. Map the `document_name` field to `Title` and `text` field to `Body`

For detailed instructions, see [Connecting to a Milvus content repository](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-connecting-milvus-content-repository).

## Troubleshooting

- **Connection Issues**: Verify your host, port, and credentials are correct
- **SSL Certificate Problems**: Ensure the certificate path is correct and the certificate is valid
- **Embedding Model Mismatch**: Confirm the same embedding model is used for both ingestion and search
- **Missing Fields**: Check that `document_name` and `text` fields are properly configured in your collection

## Conclusion

You have now successfully set up watsonx.data Milvus as a content repository for Agent Knowledge in watsonx Orchestrate on Cloud Pak for Data. Your agents can now search and retrieve information from the documents you've ingested, enhancing their capabilities with domain-specific knowledge.

For additional support or advanced configurations, refer to the official [watsonx documentation](https://www.ibm.com/docs/en/watsonx).
