# FILE: backend/twelvelabs/client.py
# This file talks to Twelve Labs API.

import os
import time
import requests
from typing import Dict, Optional

BASE_URL = "https://api.twelvelabs.io/v1.3"

def get_api_key():
    """Get API key from environment, raise error if not found"""
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    if not api_key:
        raise RuntimeError("TWELVE_LABS_API_KEY environment variable not set")
    return api_key

def get_headers():
    """Get headers with API key"""
    return {
        "x-api-key": get_api_key(),
        "Content-Type": "application/json"
    }


def upload_video(file_path: str) -> str:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)

    url = f"{BASE_URL}/assets"

    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            headers={"x-api-key": get_api_key()},
            data={"method": "direct"},
            files={"file": (os.path.basename(file_path), f, "video/mp4")},
            timeout=120
        )

    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()["id"]


def create_index(name: str) -> str:
    url = f"{BASE_URL}/indexes"
    payload = {
        "name": name,
        "engines": [
            {"name": "marengo2.6", "options": ["visual", "conversation"]}
        ]
    }

    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code != 200:
        raise RuntimeError(response.text)

    return response.json()["id"]


def index_asset(index_id: str, asset_id: str) -> None:
    url = f"{BASE_URL}/indexes/{index_id}/indexed-assets"
    response = requests.post(url, headers=get_headers(), json={"asset_id": asset_id})

    if response.status_code != 200:
        raise RuntimeError(response.text)


def wait_until_indexed(index_id: str, asset_id: str, timeout: int = 300) -> None:
    url = f"{BASE_URL}/indexes/{index_id}/indexed-assets/{asset_id}"
    start = time.time()

    while True:
        response = requests.get(url, headers=get_headers())
        status = response.json().get("status")

        if status == "ready":
            return

        if time.time() - start > timeout:
            raise TimeoutError("Indexing timed out")

        time.sleep(5)


def analyze_video(
    video_id: str,
    prompt: str,
    temperature: float = 0.2,
    stream: bool = False,
    response_format: Optional[Dict] = None,
    max_tokens: int = 2000
) -> Dict:
    """
    Analyze a video using the Twelve Labs analyze endpoint.
    
    Args:
        video_id: The unique identifier of the indexed video
        prompt: Instructions for what to analyze/generate
        temperature: Controls randomness (0-1, default 0.2)
        stream: Whether to stream the response (default False)
        response_format: Optional JSON schema for structured output
        max_tokens: Maximum tokens to generate (default 2000, max 4096)
    
    Returns:
        Dict containing the analysis results
    """
    url = f"{BASE_URL}/analyze"
    
    payload = {
        "video_id": video_id,
        "prompt": prompt,
        "temperature": temperature,
        "stream": stream,
        "max_tokens": max_tokens
    }
    
    if response_format:
        payload["response_format"] = response_format
    
    response = requests.post(url, headers=get_headers(), json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(f"Analysis failed: {response.text}")
    
    return response.json()