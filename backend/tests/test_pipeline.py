"""
FILE: backend/tests/test_pipeline.py
Corrected test file for Twelve Labs pipeline with proper pytest fixtures

Run from backend/ directory:
    python -m pytest tests/test_pipeline.py -v -s
    or
    pytest tests/test_pipeline.py -v -m "not slow"
"""

import os
import sys
import time
import pytest
from typing import Dict

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from twelvelabs.client import (
    create_index,
    create_task,
    wait_for_task,
    get_task_status,
    analyze_video
)
from twelvelabs.pipeline import analyze, analyze_existing_video


# =========================
# TEST DATASET
# =========================
TEST_VIDEO_PATH = "videos/_so-jcestGc.mp4" #DELETE 
TEST_URLS = [
    "https://www.youtube.com/shorts/_so-jcestGc",
]
TEST_PROMPTS = [
    """
    Analyze this video of a social media post describing places in Paris, France and extract ALL locations, landmarks, and places shown or mentioned.

    For each location, provide:
    1. Location name (specific as possible - e.g., "Eiffel Tower" not just "tower")
    2. Location type (landmark, restaurant, hotel, beach, mountain, city, street, etc.)
    """
]


# =========================
# HELPER FUNCTIONS
# =========================
def print_separator(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message: str):
    print(f"✅ {message}")

def print_error(message: str):
    print(f"❌ {message}")

def print_info(message: str):
    print(f"ℹ️  {message}")


# =========================
# PYTEST FIXTURES
# =========================
@pytest.fixture(scope="module")
def test_index():
    """Create a test index that will be reused across tests"""
    print_separator("FIXTURE: Creating Test Index")
    index_name = f"test-index-{int(time.time())}"
    print_info(f"Creating index: {index_name}")
    index_id = create_index(index_name)
    print_success(f"Index created: {index_id}")
    return index_id


@pytest.fixture(scope="module")
def test_task(test_index):
    """Create a test task (upload + index video)"""
    if not os.path.exists(TEST_VIDEO_PATH):
        pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
    
    print_separator("FIXTURE: Creating Test Task")
    print_info(f"Creating task for: {TEST_VIDEO_PATH}")
    task_info = create_task(test_index, TEST_VIDEO_PATH, language="en")
    task_id = task_info["task_id"]
    print_success(f"Task created: {task_id}")
    return task_id


@pytest.fixture(scope="module")
def test_video(test_task):
    """Wait for task to complete and return video_id"""
    print_separator("FIXTURE: Waiting for Task Completion")
    print_info("Waiting for indexing to complete...")
    start_time = time.time()
    video_id = wait_for_task(test_task, timeout=600, check_interval=5)
    elapsed = time.time() - start_time
    print_success(f"Task completed in {elapsed:.1f}s")
    print_success(f"Video ID: {video_id}")
    return video_id


# =========================
# BASIC TESTS (No fixtures needed)
# =========================
def test_environment():
    """Test that environment variables are set"""
    print_separator("TEST: Environment Setup")
    
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    assert api_key is not None, "TWELVE_LABS_API_KEY not set"
    
    print_success(f"API Key found: {api_key[:10]}...")


def test_create_index_standalone():
    """Test index creation (standalone test)"""
    print_separator("TEST: Create Index")
    
    index_name = f"test-standalone-{int(time.time())}"
    print_info(f"Creating index: {index_name}")
    index_id = create_index(index_name)
    
    assert index_id is not None
    assert len(index_id) > 0
    print_success(f"Index created with ID: {index_id}")


# =========================
# TESTS USING FIXTURES
# =========================
def test_index_fixture(test_index):
    """Verify the test index fixture works"""
    print_separator("TEST: Index Fixture")
    assert test_index is not None
    assert len(test_index) > 0
    print_success(f"Index fixture OK: {test_index}")


@pytest.mark.slow
def test_create_task_with_fixture(test_index):
    """Test creating a video upload/index task"""
    print_separator("TEST: Create Task")
    
    if not os.path.exists(TEST_VIDEO_PATH):
        pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
    
    print_info(f"Creating task for: {TEST_VIDEO_PATH}")
    task_info = create_task(test_index, TEST_VIDEO_PATH, language="en")
    task_id = task_info["task_id"]
    
    assert task_id is not None
    assert len(task_id) > 0
    print_success(f"Task created with ID: {task_id}")


@pytest.mark.slow
def test_get_task_status_with_fixture(test_task):
    """Test getting task status"""
    print_separator("TEST: Get Task Status")
    
    print_info(f"Checking status of task: {test_task}")
    status_data = get_task_status(test_task)
    status = status_data.get("status")
    
    assert status is not None
    assert status in ["validating", "pending", "queued", "indexing", "ready", "failed"]
    print_success(f"Task status: {status}")


@pytest.mark.slow
def test_wait_for_task_with_fixture(test_video):
    """Test that video indexing completed"""
    print_separator("TEST: Video Indexed")
    
    assert test_video is not None
    assert len(test_video) > 0
    print_success(f"Video indexed successfully: {test_video}")


@pytest.mark.slow
def test_analyze_video_with_fixture(test_video):
    """Test video analysis"""
    print_separator("TEST: Analyze Video")
    
    prompt = TEST_PROMPTS[0]
    print_info(f"Prompt: {prompt}")
    
    result = analyze_video(
        video_id=test_video,
        prompt=prompt,
        temperature=0.2,
        max_tokens=2000
    )
    
    assert result is not None
    print_success("Analysis completed!")
    print_info("Response:")
    print(result)


@pytest.mark.slow
def test_full_pipeline():
    """Test the complete pipeline (independent test)"""
    print_separator("TEST: Full Pipeline Integration")
    
    if not os.path.exists(TEST_VIDEO_PATH):
        pytest.skip(f"Test video not found: {TEST_VIDEO_PATH}")
    
    print_info("Running full pipeline")
    prompt = TEST_PROMPTS[0]
    print_info(f"Prompt: {prompt}")
    
    # Create index
    index_id = create_index(f"pipeline-test-{int(time.time())}")
    print_info(f"Index created: {index_id}")
    
    # Upload and index video
    task_info = create_task(index_id, TEST_VIDEO_PATH)
    print_info(f"Task created: {task_info['task_id']}")
    
    # Wait for indexing
    video_id = wait_for_task(task_info["task_id"], timeout=600)
    print_info(f"Video indexed: {video_id}")
    
    # Analyze
    result = analyze_existing_video(video_id, prompt)
    
    print_success("Pipeline completed!")
    print(f"\n--- Result ---")
    print(f"Video ID: {result.get('video_id')}")
    print(f"Analysis: {result.get('analysis')}")
    
    assert result.get("success") == True
    assert "analysis" in result


# =========================
# STANDALONE SCRIPT MODE
# =========================
def run_manual_tests():
    """
    Run tests manually (not through pytest).
    This is the old workflow from your original script.
    """
    print("\n" + "🚀" * 30)
    print("TWELVE LABS MANUAL TEST SUITE")
    print("🚀" * 30)
    
    # Test 1: Environment
    print_separator("Manual Test 1: Environment")
    api_key = os.getenv("TWELVE_LABS_API_KEY")
    if not api_key:
        print_error("TWELVE_LABS_API_KEY not set. Exiting.")
        return
    print_success(f"API Key found: {api_key[:10]}...")
    
    # Test 2: Create Index
    print_separator("Manual Test 2: Create Index")
    try:
        index_name = f"manual-test-{int(time.time())}"
        index_id = create_index(index_name)
        print_success(f"Index created: {index_id}")
    except Exception as e:
        print_error(f"Failed: {e}")
        return
    
    # Test 3: Create Task
    if not os.path.exists(TEST_VIDEO_PATH):
        print_error(f"Test video not found: {TEST_VIDEO_PATH}")
        print_info("Please add a video file to continue tests")
        return
    
    print_separator("Manual Test 3: Create Task")
    try:
        task_info = create_task(index_id, TEST_VIDEO_PATH)
        task_id = task_info["task_id"]
        print_success(f"Task created: {task_id}")
    except Exception as e:
        print_error(f"Failed: {e}")
        return
    
    # Test 4: Wait for Task
    print_separator("Manual Test 4: Wait for Indexing")
    try:
        video_id = wait_for_task(task_id, timeout=600)
        print_success(f"Video indexed: {video_id}")
    except Exception as e:
        print_error(f"Failed: {e}")
        return
    
    # Test 5: Analyze
    print_separator("Manual Test 5: Analyze Video")
    try:
        result = analyze_video(
            video_id=video_id,
            prompt=TEST_PROMPTS[0],
            temperature=0.2,
            max_tokens=2000
        )
        print_success("Analysis completed!")
        print(result)
    except Exception as e:
        print_error(f"Failed: {e}")
    
    print_separator("MANUAL TESTS COMPLETED")


if __name__ == "__main__":
    # When run directly (not through pytest), use manual test mode
    run_manual_tests()