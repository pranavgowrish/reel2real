# FILE: backend/twelvelabs/pipeline.py
# Corrected pipeline implementation

import os
import time
from typing import List, Dict
from .client import (
    create_index,
    create_task,
    wait_for_task,
    analyze_video
)

def download_videos(urls: List[str], output_dir: str = "videos") -> List[str]:
    """
    Download videos from URLs using yt-dlp.
    Supports YouTube, Instagram, TikTok, Twitter, and many other platforms.
    
    Args:
        urls: List of video URLs to download
        output_dir: Directory to save downloaded videos (default: "videos")
    
    Returns:
        List of paths to downloaded video files
    
    Raises:
        ImportError: If yt-dlp is not installed
        RuntimeError: If download fails
    """
    try:
        import yt_dlp
    except ImportError:
        raise ImportError(
            "yt-dlp is required for downloading videos. "
            "Install it with: pip install yt-dlp"
        )
    
    os.makedirs(output_dir, exist_ok=True)
    downloaded_files = []
    
    # Check if ffmpeg is available
    ffmpeg_available = False
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              timeout=5)
        ffmpeg_available = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Warning: ffmpeg not found. Will download pre-merged formats only.")
    
    # yt-dlp options
    if ffmpeg_available:
        # Best quality with merging (requires ffmpeg)
        format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        merge_format = 'mp4'
    else:
        # Pre-merged formats only (no ffmpeg needed)
        # This prioritizes formats that are already in MP4 with audio
        format_str = 'best[ext=mp4]/best'
        merge_format = None
    
    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'nocheckcertificate': True,
        # Only set merge format if ffmpeg is available
        'merge_output_format': merge_format,
        # Don't abort on errors, try to continue
        'ignoreerrors': False,
        # For Instagram, may need cookies
        'cookiesfrombrowser': None,
        # Instagram-specific settings
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    for i, url in enumerate(urls, 1):
        print(f"\n📥 Downloading video {i}/{len(urls)}: {url}")
        
        # Detect platform for better handling
        platform = "unknown"
        if "youtube.com" in url or "youtu.be" in url:
            platform = "youtube"
            print("   Platform: YouTube")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get the filename
                info = ydl.extract_info(url, download=False)
                
                if info is None:
                    raise RuntimeError(f"Could not extract info from URL: {url}")
                
                # Get the video ID and extension
                video_id = info.get('id', f'video_{i}')
                ext = info.get('ext', 'mp4')
                expected_file = os.path.join(output_dir, f"{video_id}.{ext}")
                
                # Download the video
                print(f"   Title: {info.get('title', 'Unknown')[:50]}...")
                if info.get('duration'):
                    print(f"   Duration: {info.get('duration')} seconds")
                print(f"   Downloading...")
                
                ydl.download([url])
                
                # Verify the file was downloaded
                if os.path.exists(expected_file):
                    file_size = os.path.getsize(expected_file) / (1024 * 1024)
                    print(f"   ✅ Downloaded: {expected_file} ({file_size:.2f} MB)")
                    downloaded_files.append(expected_file)
                else:
                    # Sometimes yt-dlp names files differently
                    # Try to find the most recently created file
                    files = [
                        os.path.join(output_dir, f) 
                        for f in os.listdir(output_dir) 
                        if f.endswith(('.mp4', '.mkv', '.webm', '.mov'))
                    ]
                    if files:
                        latest_file = max(files, key=os.path.getctime)
                        file_size = os.path.getsize(latest_file) / (1024 * 1024)
                        print(f"   ✅ Downloaded: {latest_file} ({file_size:.2f} MB)")
                        downloaded_files.append(latest_file)
                    else:
                        raise RuntimeError(f"Downloaded file not found: {expected_file}")
        
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Error downloading {url}: {error_msg}")
            
            # Provide helpful error messages
            if "login" in error_msg.lower() or "authentication" in error_msg.lower():
                print("\n   💡 TIP: This video may require authentication.")
                print("      Try using cookies from your browser.")
            
            raise RuntimeError(f"Failed to download video from {url}: {error_msg}")
    
    return downloaded_files


def analyze(video_urls: List[str], prompt: str, index_name: str = None) -> List[Dict]:
    """
    Complete pipeline: download videos, upload/index them, and analyze with prompt.
    
    Args:
        video_urls: List of video URLs to process
        prompt: The analysis prompt
        index_name: Optional index name (creates new if not provided)
    
    Returns:
        List of analysis results, one per video
    """
    # Step 1: Create or use existing index
    if not index_name:
        index_name = f"analysis-{int(time.time())}"
    
    print(f"Creating index: {index_name}")
    index_id = create_index(index_name)
    print(f"Index created: {index_id}")
    
    # Step 2: Download videos
    print(f"Downloading {len(video_urls)} video(s)...")
    video_files = download_videos(video_urls)
    
    results = []
    
    # Step 3: Upload and analyze each video
    for i, (url, file_path) in enumerate(zip(video_urls, video_files), 1):
        print(f"\n=== Processing video {i}/{len(video_urls)} ===")
        print(f"URL: {url}")
        print(f"File: {file_path}")
        
        try:
            # Create task (upload + index)
            print("Creating upload task...")
            task_info = create_task(index_id, file_path)
            task_id = task_info["task_id"]
            print(f"Task created: {task_id}")
            
            # Wait for indexing to complete
            print("Waiting for indexing to complete...")
            video_id = wait_for_task(task_id, timeout=600)
            print(f"Video indexed: {video_id}")
            
            # Analyze the video
            print(f"Analyzing with prompt: {prompt[:50]}...")
            analysis_result = analyze_video(
                video_id=video_id,
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extract the text from the response
            # The response format may vary, adjust based on actual API response
            analysis_text = analysis_result.get("data", analysis_result)
            
            results.append({
                "video_url": url,
                "video_id": video_id,
                "task_id": task_id,
                "analysis": analysis_text,
                "success": True
            })
            
            print(f"✓ Video {i} processed successfully")
            
        except Exception as e:
            print(f"✗ Error processing video {i}: {str(e)}")
            results.append({
                "video_url": url,
                "video_id": None,
                "task_id": None,
                "analysis": None,
                "success": False,
                "error": str(e)
            })
    
    return results


def analyze_existing_video(video_id: str, prompt: str) -> Dict:
    """
    Analyze an already-indexed video without re-uploading.
    
    Args:
        video_id: The ID of an already-indexed video
        prompt: The analysis prompt
    
    Returns:
        Analysis result
    """
    print(f"Analyzing video: {video_id}")
    print(f"Prompt: {prompt}")
    
    analysis_result = analyze_video(
        video_id=video_id,
        prompt=prompt,
        temperature=0.2,
        max_tokens=2000
    )
    
    return {
        "video_id": video_id,
        "analysis": analysis_result.get("data", analysis_result),
        "success": True
    }