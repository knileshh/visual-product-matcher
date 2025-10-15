#!/bin/bash

# Google Cloud Run Deployment Script
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed
# - Google Cloud project created

set -e

# Configuration
PROJECT_ID="your-gcp-project-id"  # Change this
SERVICE_NAME="visual-product-matcher"
REGION="us-central1"  # Change if needed
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "======================================"
echo "Visual Product Matcher - Cloud Run Deployment"
echo "======================================"

# Step 1: Set GCP project
echo ""
echo "Step 1: Setting GCP project..."
gcloud config set project ${PROJECT_ID}

# Step 2: Enable required APIs
echo ""
echo "Step 2: Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Step 3: Build and push Docker image
echo ""
echo "Step 3: Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo ""
echo "Step 4: Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest

# Step 5: Deploy to Cloud Run
echo ""
echo "Step 5: Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME}:latest \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "CLOUDINARY_URL=${CLOUDINARY_URL}" \
  --set-env-vars "FLASK_ENV=production"

# Step 6: Get the service URL
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test your deployment:"
echo "  Health Check: ${SERVICE_URL}/api/health"
echo "  App: ${SERVICE_URL}/"
echo "======================================"
