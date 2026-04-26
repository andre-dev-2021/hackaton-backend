import json
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

INSTANCE_URL = os.getenv("WO_INSTANCE_URL")
API_KEY = os.getenv("WO_API_KEY")

_token_cache = {"token": None, "expires_at": 0}

async def get_token() -> str:
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["token"]

    async with httpx.AsyncClient() as client:
        res = await client.request(
            method="POST",
            url="https://iam.platform.saas.ibm.com/siusermgr/api/1.0/apikeys/token",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
            },
            content=json.dumps({"apikey": API_KEY}),
        )
        
        res.raise_for_status()
        data = res.json()

    _token_cache["token"] = data["token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)

    return _token_cache["token"]