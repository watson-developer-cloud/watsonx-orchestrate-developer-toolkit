import os
import time
import requests
import json

def get_access_token(WATSONX_API_KEY):
    api_key = WATSONX_API_KEY  
    file_path = './current_token.txt'
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'accept': 'application/json'}
    data = {'grant_type': 'urn:ibm:params:oauth:grant-type:apikey',
            'apikey': api_key}

    if os.path.isfile(file_path):
        file_time = os.path.getmtime(file_path)
        if time.time() - file_time < 3600:
            print("Retrieved cached token ")
            with open(file_path, "r") as file:
                return file.read()

    response = requests.post(url, headers=headers, data=data) 

    if response.status_code == 200:
        token_data = json.loads(response.text)
        token = token_data["access_token"]

        with open(file_path, "w") as file:
            file.write(token)
        print("Retrieved new token for ")
        return token
    else:
        raise Exception("Failed to get access token")
