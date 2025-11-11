# Elasticsearch Installation and Setup Documentation

This directory contains documentation for installing and setting up Elasticsearch along with related guides and integrations.

## Elasticsearch Setup
- [Install Docker or Docker alternatives](how_to_install_docker.md): A guide explaining Docker and Docker Compose installation options, essential for running Elasticsearch-related applications.
- [Set up Elasticsearch from IBM Cloud and integrate it with watsonx Orchestrate](ICD_Elasticsearch_install_and_setup.md): Instructions for provisioning Elasticsearch instance on IBM Cloud and setting up Agent Knowledge in watsonx Orchestrate.
- [Set up watsonx Discovery (aka Elasticsearch on-prem) and integrate it with watsonx Orchestrate on-prem](watsonx_discovery_install_and_setup.md): Documentation for setting up watsonx Discovery (aka Elasticsearch on-prem) and integrating it with watsonx Orchestrate on-prem.

## Elasticsearch integration with Agent Knowledge in watsonx Orchestrate 
### Option 1: Add Knowledge to your agents in the Agent Builder UI
See [Connecting to an Elasticsearch content repository](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-connecting-elasticsearch-content-repository) in watsonx Orchestrate documentation for more details.

### Option 2: Create Knowledge bases via watsonx Orchestrate ADK (Agent Development Kit)
See [Creating external knowledge bases with Elasticsearch](https://developer.watson-orchestrate.ibm.com/knowledge_base/build_kb#elasticsearch) in ADK documentation for more details.

### Configure the Advanced Elasticsearch Settings
There are two settings under `Advanced Elasticsearch Settings` for using custom query body and custom filters to achieve advanced search use cases. See the guide [How to configure Advanced Elasticsearch Settings](./how_to_configure_advanced_elasticsearch_settings.md) for more details. 

### Federated search
You can follow the guide [here](federated_search.md) to run queries across multiple indexes within your Elasticsearch cluster.

## Document Ingestion with Elasticsearch
- [Set up the web crawler in Elasticsearch](how_to_use_web_crawler_in_elasticsearch.md): Guide for setting up and using the web crawler in Elasticsearch and connecting it to Agent Knowledge in watsonx Orchestrate.
- [Working with PDF and office documents in Elasticsearch](how_to_index_pdf_and_office_documents_elasticsearch.md): Guide for working with PDF and Office Documents in Elasticsearch, including indexing and connecting to Agent Knowledge in watsonx Orchestrate.
- [Set up text embedding models in Elasticsearch](text_embedding_deploy_and_use.md): Instructions for setting up and using 3rd-party text embeddings for dense vector search in Elasticsearch.
