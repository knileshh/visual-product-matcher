"""
Fix database entries that were incorrectly updated due to substring matching.
This script will reset cloudinary_url for products that have the wrong URL.
"""
import sqlite3
from pathlib import Path

def fix_database():
    conn = sqlite3.connect('data/products.db')
    cursor = conn.cursor()
    
    print("Analyzing database for incorrect Cloudinary URL assignments...")
    
    # Get all products with cloudinary URLs
    cursor.execute('''
        SELECT id, image_path, cloudinary_url, local_image_path 
        FROM products 
        WHERE cloudinary_url IS NOT NULL
    ''')
    products = cursor.fetchall()
    
    incorrect_count = 0
    fixed_count = 0
    
    for product_id, image_path, cloudinary_url, local_path in products:
        # Extract the filename from image_path
        if image_path:
            local_filename = Path(image_path).stem  # e.g., "11163" from "11163.jpg"
        elif local_path:
            local_filename = Path(local_path).stem
        else:
            continue
        
        # Extract the filename from cloudinary_url
        # URL format: https://res.cloudinary.com/.../visual-product-matcher/1163.jpg
        if cloudinary_url:
            cloud_filename = cloudinary_url.split('/')[-1].replace('.jpg', '')  # e.g., "1163"
        else:
            continue
        
        # Check if they match
        if local_filename != cloud_filename:
            # This product has the wrong Cloudinary URL!
            incorrect_count += 1
            print(f"Product {product_id}: {image_path} has wrong URL: {cloudinary_url}")
            
            # Option: Reset to None so it can be re-uploaded correctly
            # Or restore from local_image_path
            cursor.execute('''
                UPDATE products 
                SET cloudinary_url = NULL,
                    image_path = ?
                WHERE id = ?
            ''', (local_path or image_path, product_id))
            fixed_count += 1
    
    conn.commit()
    
    print(f"\n{'='*60}")
    print(f"Fix Summary:")
    print(f"{'='*60}")
    print(f"Products analyzed: {len(products)}")
    print(f"Incorrect assignments found: {incorrect_count}")
    print(f"Products fixed: {fixed_count}")
    
    if fixed_count > 0:
        print(f"\n✅ Database fixed! These products now need to be re-uploaded.")
        print(f"\nTo re-upload the correct images:")
        print(f"  python upload_to_cloudinary.py --workers 15 --rate-limit 0")
    else:
        print(f"\n✅ No issues found! Database is correct.")
    
    conn.close()

if __name__ == "__main__":
    print("="*60)
    print("DATABASE FIX UTILITY")
    print("="*60)
    print("\nThis will reset cloudinary_url for products that were")
    print("incorrectly matched due to substring pattern matching.")
    print("\nExample: Product 11163.jpg incorrectly got URL for 1163.jpg")
    print("\nAfter fixing, you'll need to re-upload the corrected images.")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() == 'y':
        fix_database()
    else:
        print("Cancelled.")
