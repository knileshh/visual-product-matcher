# Google Cloud Run Deployment - Windows PowerShell
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker Desktop installed and running
# - Google Cloud project created

# Configuration
$PROJECT_ID = "your-gcp-project-id"  # Change this
$SERVICE_NAME = "visual-product-matcher"
$REGION = "us-central1"  # Change if needed: us-central1, us-east1, europe-west1, asia-east1
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Visual Product Matcher - Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Step 1: Set GCP project
Write-Host "`nStep 1: Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Step 2: Enable required APIs
Write-Host "`nStep 2: Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Step 3: Configure Docker for GCR
Write-Host "`nStep 3: Configuring Docker authentication..." -ForegroundColor Yellow
gcloud auth configure-docker

# Step 4: Build Docker image
Write-Host "`nStep 4: Building Docker image..." -ForegroundColor Yellow
docker build -t "${IMAGE_NAME}:latest" .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker build failed!" -ForegroundColor Red
    exit 1
}

# Step 5: Push to Google Container Registry
Write-Host "`nStep 5: Pushing image to Google Container Registry..." -ForegroundColor Yellow
docker push "${IMAGE_NAME}:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker push failed!" -ForegroundColor Red
    exit 1
}

# Step 6: Deploy to Cloud Run
Write-Host "`nStep 6: Deploying to Cloud Run..." -ForegroundColor Yellow

# Get Cloudinary URL from .env
$CLOUDINARY_URL = (Get-Content .env | Select-String -Pattern "^CLOUDINARY_URL=").ToString().Replace("CLOUDINARY_URL=", "")

gcloud run deploy $SERVICE_NAME `
  --image "${IMAGE_NAME}:latest" `
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
    Write-Host "❌ Deployment failed!" -ForegroundColor Red
    exit 1
}

# Step 7: Get the service URL
Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan

$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
Write-Host "`nTest your deployment:" -ForegroundColor Yellow
Write-Host "  Health Check: ${SERVICE_URL}/api/health" -ForegroundColor White
Write-Host "  App: ${SERVICE_URL}/" -ForegroundColor White
Write-Host "======================================" -ForegroundColor Cyan
