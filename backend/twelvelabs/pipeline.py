# FILE: backend/twelvelabs/pipeline.py
# This file decides when and in what order to talk to Twelve Labs.

import os
from typing import List, Dict
from urllib.parse import urlparse

import yt_dlp
import instaloader

from .client import (
    upload_video,
    create_index,
    index_asset,
    wait_until_indexed,
    analyze_video
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")

def download_videos(urls: List[str]) -> List[str]:
    os.makedirs(VIDEO_DIR, exist_ok=True)
    paths: List[str] = []

    # Loop through each URL
    for i, url in enumerate(urls, start=1):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        output = os.path.join(VIDEO_DIR, f"video_{i}.mp4")

        if "youtube" in domain or "youtu.be" in domain:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': output,
                'quiet': True,
                'no_warnings': True,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                paths.append(output)
            except Exception as e:
                raise RuntimeError(f"YouTube download failed: {str(e)}")
            
            # elif "instagram.com" in domain:
            #     before = set(os.listdir(VIDEO_DIR))
            #     shortcode = parsed.path.strip("/").split("/")[-1]
            #     post = instaloader.Post.from_shortcode(loader.context, shortcode)
            #     loader.download_post(post, target=VIDEO_DIR)

            #     after = set(os.listdir(VIDEO_DIR))
            #     new_files = [f for f in after - before if f.endswith(".mp4")]

            #     if not new_files:
            #         raise RuntimeError("No Instagram video found")

            #     paths.append(os.path.join(VIDEO_DIR, new_files[0]))

    return paths


def analyze(urls: List[str], prompt: str) -> List[Dict]:
    """
    Download videos, upload to Twelve Labs, and analyze them.
    
    Args:
        urls: List of video URLs (YouTube or Instagram)
        prompt: Analysis prompt (e.g., "Identify locations shown in the video")
    
    Returns:
        List of analysis results for each video
    """
    files = download_videos(urls)
    index_id = create_index("reel-analysis-index")

    results: List[Dict] = []

    for i, file in enumerate(files):
        # Upload and index the video
        asset_id = upload_video(file)
        index_asset(index_id, asset_id)
        wait_until_indexed(index_id, asset_id)
        
        # Analyze the video with the provided prompt
        analysis = analyze_video(
            video_id=asset_id,
            prompt=prompt,
            temperature=0.2,
            stream=False,
            max_tokens=2000
        )
        
        results.append({
            "video_url": urls[i],
            "video_file": file,
            "asset_id": asset_id,
            "analysis": analysis
        })

    return results