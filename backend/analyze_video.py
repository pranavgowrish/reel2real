# FILE: backend/analyze_video.py
"""
Video analysis module - handles analyzing already-indexed videos
Extracted from test_pipeline.py

This module is for when you ALREADY have a video_id from Twelve Labs
and just want to run analysis/prompts against it without re-uploading.
"""

from typing import Dict, Optional
from twelvelabs.client import analyze_video as client_analyze_video


def analyze_existing_video(
    video_id: str,
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2000,
    response_format: Optional[Dict] = None
) -> Dict:
    """
    Analyze an already-indexed video without re-uploading.
    
    What this does:
    1. Takes a video_id that's already in Twelve Labs system
    2. Sends your prompt/question to the Twelve Labs API
    3. Gets back the AI-generated analysis response
    4. Returns formatted result dict
    
    Args:
        video_id: The ID of an already-indexed video (from previous upload)
        prompt: Your question/instructions for the AI (e.g., "Summarize this video")
        temperature: Controls randomness in AI response (0=deterministic, 1=creative)
        max_tokens: Maximum length of AI response (default 2000, max 4096)
        response_format: Optional JSON schema if you want structured output
    
    Returns:
        Dict containing:
            - video_id: The video identifier (echoed back)
            - analysis: The AI-generated response to your prompt
            - success: True if worked, False if error
            - error: Error message (only present if success=False)
    """
    print(f"Analyzing video: {video_id}")
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        # Call Twelve Labs API analyze endpoint
        # This sends the prompt to their AI model which has already processed the video
        analysis_result = client_analyze_video(
            video_id=video_id,
            prompt=prompt,
            temperature=temperature,
            stream=False,  # Get full response at once (not streaming)
            response_format=response_format,
            max_tokens=max_tokens
        )
        
        # Extract the actual text response from the API result
        # API returns nested structure, we want the "data" field
        analysis_text = analysis_result.get("data", analysis_result)
        
        # Return success response
        return {
            "video_id": video_id,
            "analysis": analysis_text,
            "success": True
        }
    
    except Exception as e:
        # If anything fails (network, API error, etc), return error response
        print(f"Error analyzing video: {str(e)}")
        return {
            "video_id": video_id,
            "analysis": None,
            "success": False,
            "error": str(e)
        }


def analyze_multiple_videos(
    video_ids: list[str],
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2000
) -> list[Dict]:
    """
    Analyze multiple already-indexed videos with the same prompt.
    
    Args:
        video_ids: List of video IDs to analyze
        prompt: The analysis prompt
        temperature: Controls randomness (0-1, default 0.2)
        max_tokens: Maximum tokens to generate (default 2000, max 4096)
    
    Returns:
        List of analysis results, one per video
    """
    results = []
    
    for i, video_id in enumerate(video_ids, 1):
        print(f"\n=== Analyzing video {i}/{len(video_ids)} ===")
        result = analyze_existing_video(
            video_id=video_id,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        results.append(result)
    
    return results