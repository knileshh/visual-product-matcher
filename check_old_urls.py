import sqlite3

conn = sqlite3.connect('data/products.db')
cursor = conn.cursor()

# Count old URLs
cursor.execute("SELECT COUNT(*) FROM products WHERE cloudinary_url NOT LIKE '%storage.googleapis.com%'")
old_urls = cursor.fetchone()[0]

# Sample old URLs
cursor.execute("SELECT cloudinary_url FROM products WHERE cloudinary_url NOT LIKE '%storage.googleapis.com%' LIMIT 5")
samples = cursor.fetchall()

print(f'🔴 Products with OLD URLs (not migrated): {old_urls}')
print(f'\n📋 Sample old URLs:')
for row in samples:
    print(f'  {row[0]}')

conn.close()
