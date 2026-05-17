import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()  

def call_blueverse_agent(agent_input: dict):
    url = os.getenv("BLUEVERSE_BASE_URL")
    token = os.getenv("BLUEVERSE_BEARER_TOKEN")
    space_name = os.getenv("BLUEVERSE_SPACE_NAME")
    flow_id = os.getenv("BLUEVERSE_FLOW_ID")

    if not all([url, token, space_name, flow_id]):
        raise Exception("BlueVerse environment variables not loaded")

    payload = {
        "query": json.dumps(agent_input),
        "space_name": space_name,
        "flowId": flow_id,
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()
