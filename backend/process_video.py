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

import os
import time
from typing import List, Dict, Optional
from twelvelabs.pipeline import download_videos
from twelvelabs.client import (
    create_index,
    create_task,
    wait_for_task,
    get_task_status,
    analyze_video as client_analyze_video
)


def download_from_urls(
    urls: List[str],
    output_dir: str = "videos"
) -> List[str]:
    """
    Download videos from URLs to local files.
    
    What this does:
    1. Uses yt-dlp library to download videos from URLs
    2. Saves them as .mp4 files in the output_dir folder
    3. Returns list of local file paths
    
    Supports: YouTube, Instagram, TikTok, Twitter, and many other platforms
    
    Args:
        urls: List of video URLs to download (e.g., YouTube links)
        output_dir: Directory to save downloaded videos (default: "videos")
    
    Returns:
        List of paths to downloaded video files (e.g., ["videos/abc123.mp4"])
    
    Raises:
        ImportError: If yt-dlp is not installed (fix: pip install yt-dlp)
        RuntimeError: If download fails (network issue, invalid URL, etc.)
    """
    print(f"Downloading {len(urls)} video(s) to {output_dir}/")
    
    try:
        # Call the download function from twelvelabs/pipeline.py
        # This handles all the yt-dlp complexity
        video_files = download_videos(urls, output_dir=output_dir)
        
        # Print success info
        print(f"\n Downloaded {len(video_files)} file(s) successfully")
        for i, file_path in enumerate(video_files, 1):
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  {i}. {file_path} ({size_mb:.2f} MB)")
        
        return video_files
    
    except ImportError as e:
        # yt-dlp not installed
        print(f"\n Error: {e}")
        print("\nInstall yt-dlp:")
        print("  pip install yt-dlp")
        raise
    
    except Exception as e:
        # Something else went wrong (bad URL, network error, etc)
        print(f"\n Download failed: {e}")
        raise


def upload_and_index_video(
    index_id: str,
    file_path: str,
    language: str = "en",
    timeout: int = 600
) -> Dict[str, str]:
    """
    Upload a local video file and index it.
    
    What this does:
    1. Takes a local .mp4 file path
    2. Uploads it to Twelve Labs using their API
    3. Waits for Twelve Labs to process/index the video (this can take several minutes)
    4. Returns the video_id once indexing is complete
    
    The "indexing" process is where Twelve Labs AI analyzes the video content
    (visual, audio, speech) so you can later query it with prompts.
    
    Args:
        index_id: The index to upload to (created via create_index())
        file_path: Path to the local video file (e.g., "videos/abc123.mp4")
        language: Video language for speech recognition (default: "en")
        timeout: Maximum time to wait for indexing in seconds (default: 600 = 10 min)
    
    Returns:
        Dict containing:
            - task_id: The task identifier (for tracking upload/index progress)
            - video_id: The indexed video identifier (use this for analysis later)
            - file_path: Original file path (echoed back)
    
    Raises:
        FileNotFoundError: If the video file doesn't exist
        TimeoutError: If indexing takes longer than timeout
        RuntimeError: If upload or indexing fails
    """
    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")
    
    print(f"Uploading: {file_path}")
    
    # Create task = upload file + start indexing
    # Twelve Labs API combines these into one operation
    task_info = create_task(index_id, file_path, language=language)
    task_id = task_info["task_id"]
    print(f"Task created: {task_id}")
    
    # Wait for indexing to complete
    # This polls the API every 5 seconds checking if status is "ready"
    print("Waiting for indexing to complete...")
    start_time = time.time()
    video_id = wait_for_task(task_id, timeout=timeout, check_interval=5)
    elapsed = time.time() - start_time
    
    print(f" Video indexed: {video_id} (took {elapsed:.1f}s)")
    
    return {
        "task_id": task_id,
        "video_id": video_id,
        "file_path": file_path
    }


def process_video_from_url(
    video_url: str,
    prompt: str,
    index_id: Optional[str] = None,
    index_name: Optional[str] = None,
    output_dir: str = "videos",
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> Dict:
    """
    Complete pipeline: download video from URL, upload/index it, and analyze.
    
    This is the FULL END-TO-END workflow for ONE video:
    1. Create/use a Twelve Labs index (storage bucket for videos)
    2. Download video from URL to local .mp4 file
    3. Upload .mp4 to Twelve Labs
    4. Wait for Twelve Labs to index/process the video
    5. Send your prompt/question to analyze the video
    6. Return the analysis result
    
    Use case: "I have a YouTube URL and want to ask a question about it"
    
    Args:
        video_url: Video URL to process (YouTube, etc.)
        prompt: Your question/instructions for the AI
        index_id: Optional existing index ID to use (if None, creates new index)
        index_name: Optional name for new index (only used if index_id is None)
        output_dir: Directory for downloaded videos (default: "videos")
        temperature: Controls randomness in AI response (0-1, default 0.2)
        max_tokens: Maximum length of AI response (default 2000)
    
    Returns:
        Dict containing:
            - video_url: Original URL (echoed back)
            - video_id: Twelve Labs video identifier
            - task_id: Upload/index task identifier
            - index_id: Index identifier used
            - file_path: Local path where video was downloaded
            - analysis: AI-generated response to your prompt
            - success: True if everything worked, False if error
            - error: Error message (only if success=False)
    """
    print(f"\n{'='*60}")
    print(f"Processing video from URL")
    print(f"{'='*60}")
    print(f"URL: {video_url}")
    
    try:
        # Step 1: Create or use existing index
        # An index is like a database/folder that holds your videos
        if not index_id:
            # No index provided, so create a new one
            if not index_name:
                # Generate a unique name with timestamp
                index_name = f"video-analysis-{int(time.time())}"
            print(f"\nCreating index: {index_name}")
            index_id = create_index(index_name)
            print(f"✓ Index created: {index_id}")
        else:
            # Using an existing index
            print(f"\nUsing existing index: {index_id}")
        
        # Step 2: Download video from URL to local file
        print(f"\nDownloading video...")
        video_files = download_from_urls([video_url], output_dir=output_dir)
        file_path = video_files[0]  # We only downloaded one video
        
        # Step 3: Upload and index the video
        # This sends the .mp4 to Twelve Labs and waits for processing
        print(f"\nUploading and indexing...")
        upload_result = upload_and_index_video(index_id, file_path)
        video_id = upload_result["video_id"]
        task_id = upload_result["task_id"]
        
        # Step 4: Analyze the video with your prompt
        # Now that video is indexed, we can ask questions about it
        print(f"\nAnalyzing video with prompt: {prompt[:100]}...")
        analysis_result = client_analyze_video(
            video_id=video_id,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract the text response from API result
        analysis_text = analysis_result.get("data", analysis_result)
        
        # Build success response with all the info
        result = {
            "video_url": video_url,
            "video_id": video_id,
            "task_id": task_id,
            "index_id": index_id,
            "file_path": file_path,
            "analysis": analysis_text,
            "success": True
        }
        
        print(f"\n Processing complete!")
        return result
    
    except Exception as e:
        # If anything failed, return error response
        print(f"\n Error processing video: {str(e)}")
        return {
            "video_url": video_url,
            "video_id": None,
            "task_id": None,
            "index_id": index_id,
            "file_path": None,
            "analysis": None,
            "success": False,
            "error": str(e)
        }


def process_multiple_videos_from_urls(
    video_urls: List[str],
    prompt: str,
    index_name: Optional[str] = None,
    output_dir: str = "videos",
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> List[Dict]:
    """
    Complete pipeline for multiple videos: download, upload/index, and analyze.
    
    This is the BATCH version of process_video_from_url():
    1. Create ONE index for all videos (more efficient than creating index per video)
    2. Download ALL videos from URLs to local .mp4 files
    3. Loop through each video:
       - Upload it to Twelve Labs
       - Wait for indexing
       - Analyze with the prompt
    4. Return list of all results
    
    Use case: "I have 20 YouTube URLs and want to ask the same question to all of them"
    
    Args:
        video_urls: List of video URLs to process
        prompt: The analysis prompt (same question for all videos)
        index_name: Optional index name (creates new if not provided)
        output_dir: Directory for downloaded videos (default: "videos")
        temperature: Controls randomness (0-1, default 0.2)
        max_tokens: Maximum tokens to generate (default 2000)
    
    Returns:
        List of result dicts, one per video (in same order as input)
        Each dict contains video_url, video_id, analysis, success, etc.
    """
    print(f"\n{'='*60}")
    print(f"Processing {len(video_urls)} videos")
    print(f"{'='*60}")
    
    # Step 1: Create ONE index for all videos
    # This is more efficient than creating separate index per video
    if not index_name:
        index_name = f"batch-analysis-{int(time.time())}"
    print(f"\nCreating index: {index_name}")
    index_id = create_index(index_name)
    print(f" Index created: {index_id}")
    
    # Step 2: Download ALL videos at once
    # Batch download is faster than one-at-a-time
    print(f"\nDownloading {len(video_urls)} video(s)...")
    try:
        video_files = download_from_urls(video_urls, output_dir=output_dir)
    except Exception as e:
        # If download fails, return error for all videos
        print(f" Download failed: {e}")
        return [{
            "video_url": url,
            "success": False,
            "error": f"Download failed: {str(e)}"
        } for url in video_urls]
    
    results = []
    
    # Step 3: Process each video (upload, index, analyze)
    for i, (url, file_path) in enumerate(zip(video_urls, video_files), 1):
        print(f"\n{'='*60}")
        print(f"Processing video {i}/{len(video_urls)}")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"File: {file_path}")
        
        try:
            # Upload and wait for indexing
            upload_result = upload_and_index_video(index_id, file_path)
            video_id = upload_result["video_id"]
            task_id = upload_result["task_id"]
            
            # Analyze with prompt
            print(f"Analyzing with prompt: {prompt[:100]}...")
            analysis_result = client_analyze_video(
                video_id=video_id,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract text response
            analysis_text = analysis_result.get("data", analysis_result)
            
            # Add success result to list
            results.append({
                "video_url": url,
                "video_id": video_id,
                "task_id": task_id,
                "index_id": index_id,
                "file_path": file_path,
                "analysis": analysis_text,
                "success": True
            })
            
            print(f" Video {i} processed successfully")
        
        except Exception as e:
            # If this video fails, log error but continue with other videos
            print(f" Error processing video {i}: {str(e)}")
            results.append({
                "video_url": url,
                "video_id": None,
                "task_id": None,
                "index_id": index_id,
                "file_path": file_path,
                "analysis": None,
                "success": False,
                "error": str(e)
            })
    
    return results


def process_local_video(
    file_path: str,
    prompt: str,
    index_id: Optional[str] = None,
    index_name: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> Dict:
    """
    Process a local video file: upload/index it and analyze.
    
    This is for when you ALREADY have a .mp4 file on disk (no download needed):
    1. Create/use a Twelve Labs index
    2. Upload the local .mp4 file to Twelve Labs
    3. Wait for Twelve Labs to index/process the video
    4. Send your prompt/question to analyze the video
    5. Return the analysis result
    
    Use case: "I already downloaded/have a video file, just need to analyze it"
    
    Args:
        file_path: Path to local video file (e.g., "videos/my_video.mp4")
        prompt: Your question/instructions for the AI
        index_id: Optional existing index ID to use (if None, creates new index)
        index_name: Optional name for new index (only used if index_id is None)
        temperature: Controls randomness in AI response (0-1, default 0.2)
        max_tokens: Maximum length of AI response (default 2000)
    
    Returns:
        Dict containing:
            - file_path: Local file path (echoed back)
            - video_id: Twelve Labs video identifier
            - task_id: Upload/index task identifier
            - index_id: Index identifier used
            - analysis: AI-generated response to your prompt
            - success: True if everything worked, False if error
            - error: Error message (only if success=False)
    """
    print(f"\n{'='*60}")
    print(f"Processing local video file")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    
    # Check if file exists first
    if not os.path.exists(file_path):
        return {
            "file_path": file_path,
            "success": False,
            "error": f"File not found: {file_path}"
        }
    
    try:
        # Step 1: Create or use existing index
        if not index_id:
            # No index provided, create new one
            if not index_name:
                index_name = f"video-analysis-{int(time.time())}"
            print(f"\nCreating index: {index_name}")
            index_id = create_index(index_name)
            print(f"✓ Index created: {index_id}")
        else:
            # Using existing index
            print(f"\nUsing existing index: {index_id}")
        
        # Step 2: Upload and index the video
        # Send .mp4 to Twelve Labs and wait for processing
        print(f"\nUploading and indexing...")
        upload_result = upload_and_index_video(index_id, file_path)
        video_id = upload_result["video_id"]
        task_id = upload_result["task_id"]
        
        # Step 3: Analyze the video with your prompt
        print(f"\nAnalyzing video with prompt: {prompt[:100]}...")
        analysis_result = client_analyze_video(
            video_id=video_id,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract text response from API result
        analysis_text = analysis_result.get("data", analysis_result)
        
        # Build success response
        result = {
            "file_path": file_path,
            "video_id": video_id,
            "task_id": task_id,
            "index_id": index_id,
            "analysis": analysis_text,
            "success": True
        }
        
        print(f"\n Processing complete!")
        return result
    
    except Exception as e:
        # If anything failed, return error response
        print(f"\n Error processing video: {str(e)}")
        return {
            "file_path": file_path,
            "video_id": None,
            "task_id": None,
            "index_id": index_id,
            "analysis": None,
            "success": False,
            "error": str(e)
        }