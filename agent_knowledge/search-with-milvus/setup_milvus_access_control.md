# How to set up granular access control for Milvus
Use this guide if you want to limit your users to only see and use certain databases or collections in watsonx.data Milvus.

## Table of contents
* [Prerequisites](#prerequisites)
* [Step 1: Add users to the watsonx.data instance](#step-1-add-users-to-the-watsonxdata-instance)
* [Step 2: Create policies and rules](#step-2-create-policies-and-rules)
* [Example: create a policy with access control at the collection level](#example-create-a-policy-with-access-control-at-the-collection-level)

## Prerequisites
### watsonx.data on-prem
* You must log in to the CPD cluster as `cpadmin`
* A watsonx.data instance is installed in the CPD cluster
* A Milvus service is created in the instance
* Create/Add users to the onprem cluster:
  - Adding users via LDAP: https://www.ibm.com/docs/en/software-hub/5.2.x?topic=users-connecting-your-identity-provider
  - to verify:
    - go to cluster homepage, for example: https://cpd-cpd.apps.rtp-7-hari-1612-wxd.cp.fyre.ibm.com/zen/?context=icp4data#/homepage
    - click "Manage users"
    - see the list of users

### watsonx.data SaaS
* You must have admin access to your watsonx.data instance
* A Milvus service is created in the instance
* Create users/service IDs/access groups in your Cloud account


## Step 1: Add users to the watsonx.data instance
### watsonx.data on-prem
1. In the cluster homepage, click the watsonx.data instance in the "My instances" section, to go to instance details page
2. In the instance details page, click on Actions -> Manage Access
3. In the access management page, click on Add users, and select the users you want to add to your watsonx.data instance
### watsonx.data SaaS
Assign access to your users/service IDs/access groups for your watsonx.data instance via IAM. For more details,
* For IBM Cloud, see [Access management in IBM Cloud](https://cloud.ibm.com/docs/account?topic=account-cloudaccess)
* For AWS, see [AWS Identity and Access Management](https://aws.amazon.com/iam/)

## Step 2: Create policies and rules
1. Open the watsonx.data console from the instance details page by clicking on "Open" in the upper right corner.
2. In the watsonx.data console, go to "Access Control" from the left-side menu
3. In the policies tab, you can start adding your policies and rules

## Example: Create a policy with access control at the collection level
### Create a collection-level policy
1. At the step to fill in "Details", fill in a name for your policy in "Policy name" -> click "Next"
2. At the step to fill in "Data objects", Choose your Milvus service -> Select the database that contains the collection of interests -> Select the collection -> Next
3. Click on Add rules -> Select all for both Managed Objects and Managed Data options -> click on Add -> Select a user
4. Review -> Create -> Click on the Activate action to activate your policy
5. Validate the access control
  * Initiate a MilvusClient in Python using the targeted username and password
    ```python
    from pymilvus import MilvusClient
    client = MilvusClient(
        uri="<your milvus service URI>", # your Milvus service URI, for example, http://localhost:19530
        user="<your username>",
        password="<your password>",
        server_pem_path="./milvus_onprem_tls.crt" # path to your SSL certificate
    )
    ```
  * client.list_databases() gives a permission error
    ```python
    client.list_databases()
    ```
    ```
    2025-10-01 19:06:47,651 [ERROR][handler]: grpc RpcError: [list_database], <_InactiveRpcError: StatusCode.PERMISSION_DENIED, Permission denied - You do not have the PrivilegeListDatabases permission to run the command. <nil> 
    ```
  * client.list_collections() gives a permission error
    ```python
    client.list_collections()
    ```
    ```
    2025-10-01 19:06:52,189 [ERROR][handler]: grpc RpcError: [list_collections], <_MultiThreadedRendezvous: StatusCode.PERMISSION_DENIED, Permission denied - You do not have the PrivilegeShowCollections permission to run the command. <nil> 
    ```
  * client.describe_collection() works
    ```python
    client.describe_collection("<your allowed collection name>")
    ```
    For example,
    ```
    {'collection_name': 'assistant_builder_docs_en_slate_30m_v2',
        'auto_id': True,
        'num_shards': 1,
        'description': '',
        'fields': [{'field_id': 100,
        'name': 'text',
        'description': '',
        'type': <DataType.VARCHAR: 21>,
        'params': {'max_length': 65535}}
    ...
    ```
    This means the targeted user can only access the collection allowed in the policy.

### Create a databases-level policy to allow list_databases()
1. At the step to fill in "Details", fill in a name for your policy in "Policy name" -> click "Next"
2. At the step to fill in "Data objects", Choose your Milvus service and do not select any databases
3. Click on Add rules -> Select the `ListDatabases` action -> click on Add -> Select a user
4. Review -> Create -> Click on the Activate action to activate your policy
5. Validate the `ListDatabases` permission
   ```python
   client.list_databases()
   ```
### Create a collections-level policy to allow list_collections() for a given database
1. At the step to fill in "Details", fill in a name for your policy in "Policy name" -> click "Next"
2. At the step to fill in "Data objects", Choose your Milvus service -> Select a database, for example, default, and do not select any collections
3. Click on Add rules -> Select the `ShowCollections` action -> click on Add -> Select a user
4. Review -> Create -> Click on the Activate action to activate your policy
5. Validate the `ShowCollections` permission
   ```python
   client.using_database("<the database you selected for the policy>")
   client.list_collections()
   ```

Now, you can use this user's credentials to set up Milvus either via watsonx Orchestrate ADK or in the Agent Builder UI.
