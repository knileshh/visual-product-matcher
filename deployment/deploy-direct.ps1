# Direct Deployment to Google Cloud Run
# Uses Google Cloud Build - no local Docker build needed!
# Prerequisites:
# - gcloud CLI installed and authenticated

# Configuration
$PROJECT_ID = "your-gcp-project-id"  # ← CHANGE THIS!
$SERVICE_NAME = "visual-product-matcher"
$REGION = "us-central1"  # us-central1, us-east1, europe-west1, asia-east1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Visual Product Matcher - Direct Cloud Deployment" -ForegroundColor Cyan
Write-Host "Building in Cloud (No local Docker needed!)" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

# Step 1: Set GCP project
Write-Host "`nStep 1: Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to set project. Check your PROJECT_ID!" -ForegroundColor Red
    exit 1
}

# Step 2: Enable required APIs
Write-Host "`nStep 2: Enabling required APIs (first time only)..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Step 3: Get Cloudinary URL from .env
Write-Host "`nStep 3: Reading Cloudinary credentials..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "   Create .env file with: CLOUDINARY_URL=cloudinary://..." -ForegroundColor Yellow
    exit 1
}

$CLOUDINARY_URL = (Get-Content .env | Select-String -Pattern "^CLOUDINARY_URL=").ToString().Replace("CLOUDINARY_URL=", "")

if ([string]::IsNullOrEmpty($CLOUDINARY_URL)) {
    Write-Host "❌ CLOUDINARY_URL not found in .env file!" -ForegroundColor Red
    exit 1
}

Write-Host "   ✅ Cloudinary credentials found" -ForegroundColor Green

# Step 4: Deploy directly to Cloud Run (Cloud Build handles Docker)
Write-Host "`nStep 4: Deploying to Cloud Run..." -ForegroundColor Yellow
Write-Host "   (This will build your Docker image in the cloud)" -ForegroundColor Cyan
Write-Host "   Estimated time: 5-10 minutes" -ForegroundColor Cyan

gcloud run deploy $SERVICE_NAME `
  --source . `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 4Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10 `
  --min-instances 0 `
  --set-env-vars "CLOUDINARY_URL=$CLOUDINARY_URL" `
  --set-env-vars "FLASK_ENV=production"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Check PROJECT_ID is correct" -ForegroundColor White
    Write-Host "  2. Ensure billing is enabled" -ForegroundColor White
    Write-Host "  3. Check you have necessary permissions" -ForegroundColor White
    Write-Host "`nView logs at: https://console.cloud.google.com/run" -ForegroundColor Cyan
    exit 1
}

# Step 5: Get the service URL
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

Write-Host "`n🎉 Your app is live!" -ForegroundColor Green
Write-Host "URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "`nTest your deployment:" -ForegroundColor Yellow
Write-Host "  Health Check: ${SERVICE_URL}/api/health" -ForegroundColor White
Write-Host "  App: ${SERVICE_URL}/" -ForegroundColor White
Write-Host "  View in Console: https://console.cloud.google.com/run" -ForegroundColor White
Write-Host "`n💡 To update, just run this script again!" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Optional: Open in browser
$response = Read-Host "`nOpen app in browser? (y/n)"
if ($response -eq 'y') {
    Start-Process $SERVICE_URL
}
