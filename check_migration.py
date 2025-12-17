import sqlite3

conn = sqlite3.connect('data/products.db')
cursor = conn.cursor()

# Check GCS URLs
cursor.execute('SELECT COUNT(*) FROM products WHERE cloudinary_url LIKE "%storage.googleapis.com%"')
gcs_count = cursor.fetchone()[0]

# Check total products
cursor.execute('SELECT COUNT(*) FROM products')
total_count = cursor.fetchone()[0]

# Sample GCS URLs
cursor.execute('SELECT cloudinary_url FROM products WHERE cloudinary_url LIKE "%storage.googleapis.com%" LIMIT 5')
sample_urls = cursor.fetchall()

print(f'✅ Products with GCS URLs: {gcs_count}')
print(f'📊 Total products: {total_count}')
print(f'\n🔗 Sample GCS URLs:')
for url in sample_urls:
    print(f'  {url[0]}')

conn.close()
