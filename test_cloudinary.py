"""
Test Cloudinary connection and upload a single image.
Run this before bulk upload to verify everything works.
"""
import os
from pathlib import Path

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

# Then import cloudinary (it will automatically read CLOUDINARY_URL)
import cloudinary
import cloudinary.uploader


def test_cloudinary_connection():
    """Test Cloudinary connection and configuration."""
    print("Testing Cloudinary configuration...\n")
    
    # Check if CLOUDINARY_URL exists
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    
    if not cloudinary_url:
        print("❌ ERROR: CLOUDINARY_URL not found in .env file")
        return False
    
    print("✓ CLOUDINARY_URL found in environment")
    
    # Parse and display config (without showing full API secret)
    try:
        # Get configuration (cloudinary automatically reads from CLOUDINARY_URL env var)
        config = cloudinary.config()
        
        if not config.cloud_name:
            print("❌ Error: Cloud name not configured")
            print(f"   CLOUDINARY_URL format: {cloudinary_url[:20]}...")
            print("\n   Expected format: cloudinary://api_key:api_secret@cloud_name")
            return False
            
        print(f"✓ Cloud name: {config.cloud_name}")
        print(f"✓ API key: {str(config.api_key)[:6]}...{str(config.api_key)[-4:]}")
        print(f"✓ API secret: {'*' * 10}")
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_upload():
    """Test uploading a single image."""
    print("\n" + "="*60)
    print("Testing single image upload...")
    print("="*60 + "\n")
    
    # Find the first image in fashion-images
    test_image = None
    fashion_dir = Path("fashion-images")
    
    # Check for nested structure
    if (fashion_dir / "fashion-images").exists():
        fashion_dir = fashion_dir / "fashion-images"
        print(f"Detected nested structure, using: {fashion_dir}")
    
    # Find first JPG image
    for img_path in fashion_dir.glob("*.jpg"):
        test_image = img_path
        break
    
    if not test_image:
        # Try uppercase
        for img_path in fashion_dir.glob("*.JPG"):
            test_image = img_path
            break
    
    if not test_image:
        print(f"❌ No test image found in {fashion_dir} directory")
        return False
    
    print(f"Using test image: {test_image.name}")
    print(f"File size: {test_image.stat().st_size / 1024:.2f} KB")
    
    try:
        # Upload to Cloudinary
        print("\nUploading to Cloudinary...")
        response = cloudinary.uploader.upload(
            str(test_image),
            folder="visual-product-matcher/test",
            public_id=f"test_{test_image.stem}",
            overwrite=True,
            resource_type="image",
            quality="auto:good",
            fetch_format="auto"
        )
        
        print("\n✅ Upload successful!")
        print(f"\nImage details:")
        print(f"  Public ID: {response['public_id']}")
        print(f"  URL: {response['url']}")
        print(f"  Secure URL: {response['secure_url']}")
        print(f"  Format: {response['format']}")
        print(f"  Width: {response['width']}px")
        print(f"  Height: {response['height']}px")
        print(f"  Size: {response['bytes'] / 1024:.2f} KB")
        
        # Clean up test upload
        print("\nCleaning up test upload...")
        cloudinary.uploader.destroy(response['public_id'])
        print("✓ Test upload deleted")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("CLOUDINARY CONNECTION TEST")
    print("="*60 + "\n")
    
    # Test connection
    if not test_cloudinary_connection():
        print("\n❌ Configuration test failed!")
        print("\nPlease check:")
        print("1. .env file exists in project root")
        print("2. CLOUDINARY_URL is set correctly")
        print("3. Format: cloudinary://api_key:api_secret@cloud_name")
        return
    
    # Test upload
    if not test_upload():
        print("\n❌ Upload test failed!")
        print("\nPlease check:")
        print("1. API credentials are correct")
        print("2. Cloudinary account is active")
        print("3. Upload quota is not exceeded")
        return
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYou can now run the bulk upload:")
    print("  python upload_to_cloudinary.py --max-uploads 10 --dry-run  # Test first")
    print("  python upload_to_cloudinary.py --max-uploads 100  # Small batch")
    print("  python upload_to_cloudinary.py  # Full upload")


if __name__ == "__main__":
    main()
