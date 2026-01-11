# FILE: backend/process_video.py
"""
Video processing module - handles downloading, uploading, indexing, and analyzing videos
Extracted from test_download.py and test_pipeline.py

This module handles the FULL PIPELINE:
- Downloading videos from URLs (YouTube, etc.) to local .mp4 files
- Uploading local .mp4 files to Twelve Labs
- Waiting for Twelve Labs to index/process them
- Analyzing the indexed videos with prompts
"""
import re 
import json
import os
import sys
import time
from typing import List, Dict, Optional
from twelvelabs.pipeline import *
from twelvelabs.client import *

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

def get_prompt(destination):
    return f"""
        Analyze this video of a social media post describing places in {destination} and extract ALL locations, landmarks, and places shown or mentioned.

        For each location, provide:
        1. Location name (specific as possible - e.g., "Eiffel Tower" not just "tower")
        """

# =========================
# HELPER FUNCTIONS 
# =========================
def validate_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL"""
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    return any(domain in url.lower() for domain in youtube_domains)

def test_environment():
    """Test that environment variables are set"""
    print("TEST: Environment Setup")
    
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    assert api_key is not None, "TWELVE_LABS_API_KEY not set"
    
    print(f"API Key found: {api_key[:10]}...")


# ======================================
# MAIN FUNCTION - TAKES IN A SINGLE URL
# ======================================
def fully_process(url: str, destination: str) -> List[str]:
    print("=" * 70)
    print(" YOUTUBE VIDEO DOWNLOAD")
    print("=" * 70)
    
    # Validate all URLs are YouTube
    print("\n Validating URL...")
    if not validate_youtube_url(url):
        print(f" ERROR: Not a YouTube URL: {url}")
        print("This only supports YouTube videos!")
        return []
    print(f"   {url}")
    
    print(f"\n Downloading YouTube video:")
    print(f" Video URL: {url}")
    
    print("\n Starting downloads...")
    # files = []
    files = list(download_videos([url], output_dir="videos"))
        
    print("\n" + "=" * 70)
    print(" DOWNLOAD COMPLETE")
    print("=" * 70)

        
    print(f"\n Downloaded file:")
    
    location_names = []
        
    try: 
        if len(files) > 0:
            video_path = files[0]
        else:
            raise Exception("No video files found")
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f" {video_path}")
            print(f"     Size: {size_mb:.2f} MB")
        else:
            print(f" {video_path} (NOT FOUND)")
        
        print("\n Download successful!")
        print("\n Next steps:")
        print("  1. Check the 'videos' folder for downloaded files")
        print("  2. Run: pytest tests/test_pipeline.py -v -s -m slow")
        print("  3. Or run: python test_quick.py videos/<filename>.mp4")
        
        
        """
        Analyze video 
        """
        print("\n" + "" * 30)
        print("TWELVE LABS")
        print("" * 30)
        
        # 1: Environment
        print("1: Environment")
        api_key = os.getenv("TWELVE_LABS_API_KEY")
        if not api_key:
            print("TWELVE_LABS_API_KEY not set. Exiting.")
            return []
        print(f"API Key found: {api_key[:10]}...")
        
        # 2: Create Index
        print("2: Create Index")
        try:
            index_name = f"manual-test-{int(time.time())}"
            index_id = create_index(index_name)
            print(f"Index created: {index_id}")
        except Exception as e:
            print(f"Failed: {e}")
            return []
        
        # 3: Create Task
        if not os.path.exists(video_path):
            print(f"Test video not found: {video_path}")
            print("Please add a video file to continue tests")
            return []
            
        print("3: Create Task")
        try:
            task_info = create_task(index_id, video_path)
            task_id = task_info["task_id"]
            print(f"Task created: {task_info['task_id']}")
        except Exception as e:
            print(f"Failed: {e}")
            return []
            
        # 4: Wait for Task
        print("4: Wait for Indexing")
        try:
            video_id = wait_for_task(task_info["task_id"], timeout=60)
            print(f"Video indexed: {video_id}")
        except Exception as e:
            print(f"Failed: {e}")
            return []
            
        # 5: Analyze    
        result = analyze_existing_video(video_id, get_prompt(destination))
            
        print(f"Youtube video pipeline completed!")
        print(f"\n--- Result ---")
        print(f"Video ID: {result.get('video_id')}")
        print(f"Analysis: {result.get('analysis')}")
            
        assert result.get("success") == True

        #extract locations from analysis 
        analysis = result.get("analysis", "")
        # Pattern to match text between ** **
        pattern = r'\*\*(.*?)\*\*'
        # Find all matches
        location_names = re.findall(pattern, analysis)
        return location_names

    except ImportError as e:
        print("\n ERROR: yt-dlp not installed")
        print("\n Install it with:")
        print("  pip install yt-dlp")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        return []
    
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n TROUBLESHOOTING:")
        print("  1. Install ffmpeg for better quality:")
        print("     choco install ffmpeg")
        print("  2. Some videos may be region-restricted")
        print("  3. Check your internet connection")
        return []

    
    print("COMPLETED")
    return []


if __name__ == "__main__":
    # When run directly (not through pytest)
    print("\n RUNNING FULL VIDEO PROCESSING/ANALYSIS PIPELINE \n")
    # fully_process(video_url)
    print("\n PROCESSING AND ANALYSIS COMPLETE \n")


