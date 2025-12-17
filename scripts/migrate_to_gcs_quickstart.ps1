# Google Cloud Storage Migration - Quick Start
# Run this script to migrate from Cloudinary to GCS

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "Google Cloud Storage Migration Tool" -ForegroundColor Cyan
Write-Host "Visual Product Matcher - Image Migration" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
Write-Host "[1/6] Checking Google Cloud SDK..." -ForegroundColor Yellow
$gcloudCommand = Get-Command gcloud -ErrorAction SilentlyContinue

if (-not $gcloudCommand) {
    Write-Host "✗ Google Cloud SDK not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Google Cloud SDK:" -ForegroundColor Yellow
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "After installation, run:" -ForegroundColor Yellow
    Write-Host "  gcloud auth login" -ForegroundColor Cyan
    Write-Host "  gcloud auth application-default login" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Google Cloud SDK installed" -ForegroundColor Green

# Check if authenticated
Write-Host ""
Write-Host "[2/6] Checking authentication..." -ForegroundColor Yellow
$authCheck = & gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
$authAccount = $authCheck | Where-Object { $_ -notmatch 'WARNING' -and $_ -notmatch 'Listed' } | Select-Object -First 1

if (-not $authAccount -or $authAccount -eq "") {
    Write-Host "✗ Not authenticated with Google Cloud" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host "  gcloud auth login" -ForegroundColor Cyan
    Write-Host "  gcloud auth application-default login" -ForegroundColor Cyan
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "✓ Authenticated as: $authAccount" -ForegroundColor Green

# Get project ID
Write-Host ""
Write-Host "[3/6] Getting project information..." -ForegroundColor Yellow
$projectCheck = & gcloud config get-value project 2>&1
$projectId = $projectCheck | Where-Object { $_ -notmatch 'WARNING' -and $_ -notmatch 'unset' -and $_ -ne "" } | Select-Object -First 1

if (-not $projectId -or $projectId -eq "(unset)") {
    Write-Host "! No project set" -ForegroundColor Yellow
    $projectId = Read-Host "Enter your Google Cloud Project ID"
    & gcloud config set project $projectId 2>&1 | Out-Null
}

Write-Host "✓ Project ID: $projectId" -ForegroundColor Green

# Get bucket name
Write-Host ""
Write-Host "[4/6] Configure GCS bucket..." -ForegroundColor Yellow
$defaultBucket = "visual-product-matcher-images"
$bucketInput = Read-Host "Enter bucket name (press Enter for '$defaultBucket')"

if ([string]::IsNullOrWhiteSpace($bucketInput)) {
    $bucketName = $defaultBucket
} else {
    $bucketName = $bucketInput
}

Write-Host "✓ Bucket name: $bucketName" -ForegroundColor Green

# Check if bucket exists, create if not
Write-Host ""
Write-Host "[5/6] Checking bucket..." -ForegroundColor Yellow

$bucketCheck = & gsutil ls -b gs://$bucketName 2>&1
$bucketExists = $bucketCheck -notmatch "BucketNotFoundException" -and $bucketCheck -match "gs://"

if (-not $bucketExists) {
    Write-Host "! Bucket doesn't exist. Creating..." -ForegroundColor Yellow
    
    $locationInput = Read-Host "Enter location (press Enter for 'us-central1' - cheapest)"
    $location = if ([string]::IsNullOrWhiteSpace($locationInput)) { "us-central1" } else { $locationInput }
    
    Write-Host "  Creating bucket in $location..." -ForegroundColor Yellow
    & gcloud storage buckets create gs://$bucketName --location=$location --uniform-bucket-level-access 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Bucket created" -ForegroundColor Green
        
        # Make bucket public
        Write-Host "  Making bucket public..." -ForegroundColor Yellow
        & gcloud storage buckets add-iam-policy-binding gs://$bucketName --member=allUsers --role=roles/storage.objectViewer 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Bucket is now public" -ForegroundColor Green
        } else {
            Write-Host "⚠ Could not set public policy automatically" -ForegroundColor Yellow
            Write-Host "  You may need to make the bucket public manually" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Failed to create bucket" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "✓ Bucket exists" -ForegroundColor Green
}

# Check Python dependencies
Write-Host ""
Write-Host "[6/6] Checking Python dependencies..." -ForegroundColor Yellow

python -c "import google.cloud.storage" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "! google-cloud-storage not installed. Installing..." -ForegroundColor Yellow
    pip install google-cloud-storage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "✓ Dependencies already installed" -ForegroundColor Green
}

# All checks passed
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host ""

# Ask what to do
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "  1. Dry run (test without uploading)" -ForegroundColor White
Write-Host "  2. Upload 50 images (test)" -ForegroundColor White
Write-Host "  3. Upload ALL images (42,700)" -ForegroundColor White
Write-Host "  4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running DRY RUN (no actual uploads)..." -ForegroundColor Yellow
        python scripts\migrate_to_gcs.py --project-id $projectId --bucket-name $bucketName --max-uploads 10 --dry-run
    }
    "2" {
        Write-Host ""
        Write-Host "Uploading 50 images as test..." -ForegroundColor Yellow
        python scripts\migrate_to_gcs.py --project-id $projectId --bucket-name $bucketName --max-uploads 50
    }
    "3" {
        Write-Host ""
        Write-Host "⚠️  This will upload ALL 42,700 images!" -ForegroundColor Yellow
        Write-Host "   Estimated time: 30-60 minutes" -ForegroundColor Yellow
        Write-Host "   Estimated cost: ~`$0.20/month storage" -ForegroundColor Yellow
        Write-Host ""
        $confirm = Read-Host "Are you sure? (yes/no)"
        
        if ($confirm -eq "yes") {
            Write-Host ""
            Write-Host "Starting full migration..." -ForegroundColor Green
            python scripts\migrate_to_gcs.py --project-id $projectId --bucket-name $bucketName --workers 20
        } else {
            Write-Host "Migration cancelled" -ForegroundColor Yellow
        }
    }
    "4" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "Invalid choice" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "Migration script completed!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test your application locally: python app.py" -ForegroundColor White
Write-Host "  2. Update Cloud Run environment variables:" -ForegroundColor White
Write-Host "     GCS_PROJECT_ID=$projectId" -ForegroundColor Gray
Write-Host "     GCS_BUCKET_NAME=$bucketName" -ForegroundColor Gray
Write-Host "  3. Deploy to Cloud Run" -ForegroundColor White
Write-Host ""
Write-Host "Images are now served from:" -ForegroundColor Cyan
Write-Host "  https://storage.googleapis.com/$bucketName/products/" -ForegroundColor Gray
Write-Host ""
Write-Host "For detailed guide, see: docs\GCS_MIGRATION_GUIDE.md" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
