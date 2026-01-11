# FILE: backend/twelvelabs/client.py
# Corrected implementation for Twelve Labs API v1.3

import os
import time
import requests
from typing import Dict, Optional


BASE_URL = "https://api.twelvelabs.io/v1.3"

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("TWELVE_LABS_API_KEY")
if not api_key:
    raise RuntimeError("TWELVE_LABS_API_KEY environment variable not set")


def get_headers():
    """Get headers with API key"""
    return {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }


def create_index(name: str) -> str:
    """Create a new index and return the index ID"""
    url = f"{BASE_URL}/indexes"
    payload = {
        "index_name": name,
        "models": [
            # {"model_name": "marengo2.7", "model_options": ["visual", "audio"]},
            {"model_name": "pegasus1.2", "model_options": ["visual", "audio"]}
        ]
    }

    response = requests.post(url, headers=get_headers(), json=payload)
    if response.status_code not in [200, 201]:
        raise RuntimeError(f"Index creation failed: {response.text}")

    result = response.json()
    # API returns "_id" not "id"
    return result.get("id")


def create_task(index_id: str, file_path: str, language: str = "en") -> Dict[str, str]:
    """
    Upload and index a video in one operation using the tasks endpoint.
    This replaces the old upload_video + index_asset pattern.
    
    Returns:
        Dict with keys: 'task_id' and 'video_id' (once ready)
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    url = f"{BASE_URL}/tasks"
    
    # Note: When uploading a file, we don't use JSON content type
    headers = {"x-api-key": api_key}
    
    with open(file_path, "rb") as f:
        files = {"video_file": (os.path.basename(file_path), f, "video/mp4")}
        data = {
            "index_id": index_id,
            "language": language
        }
        
        response = requests.post(
            url,
            headers=headers,
            data=data,
            files=files,
            timeout=120
        )

    if response.status_code not in [200, 201]:
        raise RuntimeError(f"Task creation failed: {response.text}")

    result = response.json()
    # API may return "_id" or "id" for task_id
    task_id = result.get("_id") or result.get("id")
    video_id = result.get("video_id")
    
    return {
        "task_id": task_id,
        "video_id": video_id
    }


def get_task_status(task_id: str) -> Dict:
    """Get the current status of a video indexing task"""
    url = f"{BASE_URL}/tasks/{task_id}"
    response = requests.get(url, headers=get_headers())
    
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get task status: {response.text}")
    
    return response.json()


def wait_for_task(task_id: str, timeout: int = 600, check_interval: int = 5) -> str:
    """
    Wait for a video indexing task to complete.
    
    Args:
        task_id: The task identifier
        timeout: Maximum time to wait in seconds (default 10 minutes)
        check_interval: How often to check status in seconds
    
    Returns:
        video_id: The unique identifier of the indexed video
    """
    start = time.time()
    
    while True:
        if time.time() - start > timeout:
            raise TimeoutError(f"Task indexing timed out after {timeout}s")
        
        task_data = get_task_status(task_id)
        status = task_data.get("status")
        
        print(f"Task {task_id}: {status}")
        
        if status == "ready":
            video_id = task_data.get("video_id")
            if not video_id:
                raise RuntimeError("Task completed but no video_id returned")
            return video_id
        
        if status in ["failed", "error"]:
            error_msg = task_data.get("message", "Unknown error")
            raise RuntimeError(f"Task failed: {error_msg}")
        
        # Status is validating, pending, queued, or indexing
        time.sleep(check_interval)


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


# Legacy wrapper functions for backward compatibility
def upload_video(file_path: str) -> str:
    """
    DEPRECATED: Use create_task() instead.
    This function is kept for backward compatibility only.
    """
    raise DeprecationWarning(
        "upload_video() is deprecated. Use create_task() + wait_for_task() instead."
    )


def index_asset(index_id: str, asset_id: str) -> None:
    """
    DEPRECATED: No longer needed in v1.3 API.
    Use create_task() which handles upload + indexing together.
    """
    raise DeprecationWarning(
        "index_asset() is deprecated. Use create_task() which handles indexing automatically."
    )


def wait_until_indexed(index_id: str, asset_id: str, timeout: int = 300) -> None:
    """
    DEPRECATED: Use wait_for_task() instead.
    """
    raise DeprecationWarning(
        "wait_until_indexed() is deprecated. Use wait_for_task() instead."
    )