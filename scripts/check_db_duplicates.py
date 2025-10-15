import sqlite3

conn = sqlite3.connect('data/products.db')
cursor = conn.cursor()

# Check for duplicate image paths
cursor.execute('''
    SELECT image_path, COUNT(*) as cnt 
    FROM products 
    GROUP BY image_path 
    HAVING cnt > 1 
    LIMIT 10
''')
duplicates = cursor.fetchall()

print('Sample duplicate image paths:')
if duplicates:
    for path, count in duplicates:
        print(f'  {path}: {count} times')
else:
    print('  No duplicates found!')

# Check total stats
cursor.execute('SELECT COUNT(*) FROM products')
total = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT image_path) FROM products')
unique_paths = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM products WHERE cloudinary_url IS NOT NULL')
with_cloudinary = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(DISTINCT cloudinary_url) FROM products WHERE cloudinary_url IS NOT NULL')
unique_cloudinary = cursor.fetchone()[0]

print(f'\nDatabase Statistics:')
print(f'  Total products: {total}')
print(f'  Unique image paths: {unique_paths}')
print(f'  Products with cloudinary_url: {with_cloudinary}')
print(f'  Unique cloudinary URLs: {unique_cloudinary}')

# Check for pattern matching issues
print(f'\nChecking for potential duplicate updates...')
cursor.execute('''
    SELECT cloudinary_url, COUNT(*) as cnt 
    FROM products 
    WHERE cloudinary_url IS NOT NULL
    GROUP BY cloudinary_url 
    HAVING cnt > 1 
    LIMIT 5
''')
cloud_dupes = cursor.fetchall()

if cloud_dupes:
    print('Found products sharing same Cloudinary URL:')
    for url, count in cloud_dupes:
        print(f'  {url}: {count} products')
        cursor.execute('SELECT id, image_path FROM products WHERE cloudinary_url = ?', (url,))
        products = cursor.fetchall()
        for pid, path in products[:3]:
            print(f'    - Product {pid}: {path}')
else:
    print('No duplicate Cloudinary URLs found')

conn.close()
