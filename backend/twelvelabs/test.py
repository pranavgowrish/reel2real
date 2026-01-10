import requests 
import os
from twelvelabs import *
from typing import Dict

#code to get URLs from webscraping, either connect to a file or add this code below such a file
#have to put these URLs in a list while scraping 

#code to traverse list and download these URLs into mp4 files and store them in a folder in the repo
def scrape_video_urls(video_urls: list[str]) -> list[str]:
    #take this list of urls, download each, store them in a folder in the repo, return list of file paths
    downloaded_files = []

    return downloaded_files

#code to traverse folder of videos and using twelve labs API to analyse them 
#   by prompting it to retrieve locations/places based on the user's input 
#creating asset = uploading file to platform to be able to analyse it
TWELVE_LABS_API_KEY = os.getenv("TWELVE_LABS_API_KEY")  
UPLOAD_URL = "https://api.twelvelabs.io/v1.3/assets"

def upload_video(file_path: str) -> Dict:
    """
    Uploads a video to Twelve Labs and returns asset metadata.
    Raises exception if upload fails.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Video not found: {file_path}")

    headers = {
        "x-api-key": TWELVE_LABS_API_KEY
    }

    payload = {
        "method": "direct"
    }

    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f, "video/mp4")
        }

        response = requests.post(
            UPLOAD_URL,
            headers=headers,
            data=payload,
            files=files,
            timeout=120
        )

    if response.status_code != 200:
        raise RuntimeError(f"Twelve Labs upload failed: {response.text}")

    data = response.json()

    if "id" not in data:
        raise RuntimeError(f"Unexpected Twelve Labs response: {data}")

    return data
