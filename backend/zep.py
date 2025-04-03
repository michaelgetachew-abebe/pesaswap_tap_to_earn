import os
import uuid
from zep_cloud.client import Zep # type: ignore
from dotenv import load_dotenv
import httpx # Just in case for ssl

ZEP_API_KEY = os.environ.get("ZEP_API_KEY") # This API Key should be part of the docker file when creating the image for the backend service


def create_zep_client(key):
    return Zep(api_key=key)

def add_user(user_id: str, email: str = None, first_name: str = None, last_name:str = None) -> None:
    
    client = create_zep_client(key=ZEP_API_KEY)

    client.user.add(
        user_id=user_id,
        email="",
        first_name="",
        last_name=""
    )

    return

def create_user_session(user_id: str) -> None:
    client = create_zep_client(key=ZEP_API_KEY)

    session_id = user_id + "_" + uuid.uuid4() 
    
    client.memory.add_session(session_id, user_id)

    return

# Customize the memory context string to better enrich the prompt for the Agent
def create_context_string():
    pass