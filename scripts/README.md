# Scripts Directory

Utility scripts for development, testing, and maintenance.

## 🆕 NEW: Image Migration to Google Cloud Storage

### `migrate_to_gcs_quickstart.ps1` ⭐ **RECOMMENDED**
Interactive PowerShell wizard for migrating to GCS.

```powershell
.\scripts\migrate_to_gcs_quickstart.ps1
```

- Checks prerequisites automatically
- Guides through GCS bucket creation
- Offers dry-run testing
- Handles full migration process

### `migrate_to_gcs.py`
Python script for batch GCS uploads.

```bash
# Test without uploading
python scripts/migrate_to_gcs.py --project-id YOUR_ID --bucket-name your-bucket --dry-run

# Full migration
python scripts/migrate_to_gcs.py --project-id YOUR_ID --bucket-name your-bucket --workers 20
```

**See:** `docs/GCS_MIGRATION_GUIDE.md` for complete documentation.

---

## 🧪 Testing Scripts

### API Testing
- **quick_api_test.py** - Quick API endpoint testing (run while server is running)
- **test_api_endpoints.py** - Comprehensive API endpoint testing suite
- **test_cloudinary.py** - Cloudinary integration testing

**Usage:**
```bash
# Start the server first
python app.py

# Then in another terminal, run tests
python scripts/quick_api_test.py
```

## 🔧 Utility Scripts

### Data Initialization
- **init_data.py** - Initialize database and build search index

**Usage:**
```bash
python scripts/init_data.py
```

### Cloudinary Migration
- **upload_to_cloudinary.py** - Upload images to Cloudinary with parallel processing

**Usage:**
```bash
# Upload with default settings
python scripts/upload_to_cloudinary.py

# Custom settings
python scripts/upload_to_cloudinary.py --max-uploads 300 --workers 15
```

### Database Maintenance
- **fix_database.py** - Fix database issues and inconsistencies

**Usage:**
```bash
python scripts/fix_database.py
```

## 📝 Notes

- All scripts should be run from the project root directory
- Make sure your virtual environment is activated
- Environment variables (`.env`) must be configured for Cloudinary scripts
