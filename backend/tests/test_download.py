"""
FILE: backend/tests/test_download.py
Test script for downloading YouTube videos ONLY

Usage from backend/ directory:
    python tests/test_download.py
    or
    pytest tests/test_download.py -v -s
"""

import sys
import os

# Add parent directory (backend/) to path so we can import twelvelabs
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from twelvelabs.pipeline import download_videos

# Test URLs - YOUTUBE ONLY
TEST_URLS = [
    "https://youtube.com/shorts/VqBRHig7bR4?si=iABBABS4_79IPwaX"
]


def validate_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL"""
    youtube_domains = ['youtube.com', 'youtu.be', 'm.youtube.com']
    return any(domain in url.lower() for domain in youtube_domains)


def test_download_youtube():
    """Test downloading videos from YouTube ONLY (pytest compatible)"""
    
    # Import pytest only when running as a test
    import pytest
    
    print("\n" + "=" * 70)
    print(" YOUTUBE VIDEO DOWNLOAD TEST")
    print("=" * 70)
    
    # Validate all URLs are YouTube
    print("\n Validating URLs...")
    for url in TEST_URLS:
        if not validate_youtube_url(url):
            pytest.fail(f" Not a YouTube URL: {url}\nThis test only supports YouTube videos!")
        print(f"   {url}")
    
    print(f"\n Downloading {len(TEST_URLS)} YouTube video(s):")
    for i, url in enumerate(TEST_URLS, 1):
        print(f"  {i}. {url}")
    
    try:
        print("\n Starting downloads...")
        files = download_videos(TEST_URLS, output_dir="videos")
        
        print("\n" + "=" * 70)
        print(" DOWNLOAD COMPLETE")
        print("=" * 70)
        
        assert len(files) == len(TEST_URLS), f"Expected {len(TEST_URLS)} files, got {len(files)}"
        
        print(f"\n Downloaded {len(files)} file(s):")
        for i, file_path in enumerate(files, 1):
            assert os.path.exists(file_path), f"File not found: {file_path}"
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  {i}. {file_path}")
            print(f"     Size: {size_mb:.2f} MB")
        
        print("\n All downloads successful!")
        print("\n Next steps:")
        print("  1. Check the 'videos' folder for downloaded files")
        print("  2. Run: pytest tests/test_pipeline.py -v -s -m slow")
        print("  3. Or run: python test_quick.py videos/<filename>.mp4")
        
    except ImportError as e:
        print(f"\n ERROR: {e}")
        print("\n Install yt-dlp:")
        print("  pip install yt-dlp")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        pytest.skip(f"yt-dlp not installed: {e}")
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n TROUBLESHOOTING:")
        print("  1. Install ffmpeg for better quality:")
        print("     choco install ffmpeg")
        print("  2. Some videos may be region-restricted")
        print("  3. YouTube may require authentication for age-restricted content")
        print("  4. Check your internet connection")
        
        raise


def manual_test():
    """Manual test mode (non-pytest)"""
    
    print("=" * 70)
    print(" YOUTUBE VIDEO DOWNLOAD TEST (Manual Mode)")
    print("=" * 70)
    
    # Validate all URLs are YouTube
    print("\n Validating URLs...")
    for url in TEST_URLS:
        if not validate_youtube_url(url):
            print(f" ERROR: Not a YouTube URL: {url}")
            print("This test only supports YouTube videos!")
            return []
        print(f"   {url}")
    
    print(f"\n Downloading {len(TEST_URLS)} YouTube video(s):")
    for i, url in enumerate(TEST_URLS, 1):
        print(f"  {i}. {url}")
    
    try:
        print("\n Starting downloads...")
        files = download_videos(TEST_URLS, output_dir="videos")
        
        print("\n" + "=" * 70)
        print(" DOWNLOAD COMPLETE")
        print("=" * 70)
        
        print(f"\n Downloaded {len(files)} file(s):")
        for i, file_path in enumerate(files, 1):
            if os.path.exists(file_path):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  {i}. {file_path}")
                print(f"     Size: {size_mb:.2f} MB")
            else:
                print(f"  {i}. {file_path} (NOT FOUND)")
        
        print("\n All downloads successful!")
        print("\n Next steps:")
        print("  1. Check the 'videos' folder for downloaded files")
        print("  2. Run: pytest tests/test_pipeline.py -v -s -m slow")
        print("  3. Or run: python test_quick.py videos/<filename>.mp4")
        
        return files
        
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


if __name__ == "__main__":
    # When run directly (not through pytest)
    print("\n  NOTE: This test ONLY works with YouTube URLs")
    print("For Instagram, use: python tests/test_instagram.py\n")
    manual_test()