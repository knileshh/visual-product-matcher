@echo off
REM Simple Migration Script for Windows
REM This script guides you through migrating images to Google Cloud Storage

echo.
echo ================================================================================
echo Google Cloud Storage Migration Tool
echo Visual Product Matcher - Image Migration
echo ================================================================================
echo.

REM Check if gcloud is installed
echo [1/6] Checking Google Cloud SDK...
where gcloud >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Google Cloud SDK not found!
    echo.
    echo Please install Google Cloud SDK from:
    echo https://cloud.google.com/sdk/docs/install
    echo.
    echo After installation, run:
    echo   gcloud auth login
    echo   gcloud auth application-default login
    echo.
    pause
    exit /b 1
)
echo [OK] Google Cloud SDK installed
echo.

REM Check authentication
echo [2/6] Checking authentication...
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Not authenticated with Google Cloud
    echo.
    echo Please run:
    echo   gcloud auth login
    echo   gcloud auth application-default login
    echo.
    pause
    exit /b 1
)
echo [OK] Authenticated
echo.

REM Get project ID
echo [3/6] Getting project information...
for /f "delims=" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

if "%PROJECT_ID%"=="" (
    echo [WARNING] No project set
    set /p PROJECT_ID="Enter your Google Cloud Project ID: "
    gcloud config set project %PROJECT_ID%
)
echo [OK] Project ID: %PROJECT_ID%
echo.

REM Get bucket name
echo [4/6] Configure GCS bucket...
set BUCKET_NAME=visual-product-matcher-images
set /p INPUT_BUCKET="Enter bucket name (press Enter for '%BUCKET_NAME%'): "
if not "%INPUT_BUCKET%"=="" set BUCKET_NAME=%INPUT_BUCKET%
echo [OK] Bucket name: %BUCKET_NAME%
echo.

REM Check if bucket exists
echo [5/6] Checking bucket...
gsutil ls -b gs://%BUCKET_NAME% >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Bucket doesn't exist. Creating...
    set LOCATION=us-central1
    set /p INPUT_LOCATION="Enter location (press Enter for 'us-central1'): "
    if not "%INPUT_LOCATION%"=="" set LOCATION=%INPUT_LOCATION%
    
    gcloud storage buckets create gs://%BUCKET_NAME% --location=%LOCATION% --uniform-bucket-level-access
    
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Bucket created
        echo [INFO] Making bucket public...
        gcloud storage buckets add-iam-policy-binding gs://%BUCKET_NAME% --member=allUsers --role=roles/storage.objectViewer
        if %ERRORLEVEL% EQU 0 (
            echo [OK] Bucket is now public
        )
    ) else (
        echo [ERROR] Failed to create bucket
        pause
        exit /b 1
    )
) else (
    echo [OK] Bucket exists
)
echo.

REM Check Python dependencies
echo [6/6] Checking Python dependencies...
python -c "import google.cloud.storage" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] google-cloud-storage not installed. Installing...
    pip install google-cloud-storage
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)
echo.

REM All checks passed
echo ================================================================================
echo [SUCCESS] Setup Complete!
echo ================================================================================
echo.

REM Ask what to do
echo What would you like to do?
echo   1. Dry run (test without uploading)
echo   2. Upload 50 images (test)
echo   3. Upload ALL images (42,700)
echo   4. Exit
echo.
set /p CHOICE="Enter choice (1-4): "

if "%CHOICE%"=="1" (
    echo.
    echo Running DRY RUN (no actual uploads)...
    python scripts\migrate_to_gcs.py --project-id %PROJECT_ID% --bucket-name %BUCKET_NAME% --max-uploads 10 --dry-run
) else if "%CHOICE%"=="2" (
    echo.
    echo Uploading 50 images as test...
    python scripts\migrate_to_gcs.py --project-id %PROJECT_ID% --bucket-name %BUCKET_NAME% --max-uploads 50
) else if "%CHOICE%"=="3" (
    echo.
    echo [WARNING] This will upload ALL 42,700 images!
    echo   Estimated time: 30-60 minutes
    echo   Estimated cost: ~$0.20/month storage
    echo.
    set /p CONFIRM="Are you sure? (yes/no): "
    if /i "%CONFIRM%"=="yes" (
        echo.
        echo Starting full migration...
        python scripts\migrate_to_gcs.py --project-id %PROJECT_ID% --bucket-name %BUCKET_NAME% --workers 20
    ) else (
        echo Migration cancelled
    )
) else if "%CHOICE%"=="4" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Migration script completed!
echo ================================================================================
echo.
echo Next steps:
echo   1. Test your application locally: python app.py
echo   2. Update Cloud Run environment variables:
echo      GCS_PROJECT_ID=%PROJECT_ID%
echo      GCS_BUCKET_NAME=%BUCKET_NAME%
echo   3. Deploy to Cloud Run
echo.
echo Images are now served from:
echo   https://storage.googleapis.com/%BUCKET_NAME%/products/
echo.
echo For detailed guide, see: docs\GCS_MIGRATION_GUIDE.md
echo.
pause
