# Deployment Directory

Docker and deployment configuration files.

## 📦 Files

### Docker
- **Dockerfile** - Docker container definition
- **.dockerignore** - Files to exclude from Docker build
- **gunicorn_config_cloud.py** - Production WSGI server configuration

## 🚀 Quick Deployment

### Build Docker Image
```bash
docker build -t visual-matcher:latest .
```

### Test Locally
```bash
docker run -d \
  --name visual-matcher-test \
  -p 8080:8080 \
  --env-file .env \
  visual-matcher:latest

# Check health
curl http://localhost:8080/api/health

# View logs
docker logs visual-matcher-test

# Stop and remove
docker stop visual-matcher-test
docker rm visual-matcher-test
```

### Deploy to Railway

**Option 1: Docker Hub**
```bash
# Login and push
docker login
docker tag visual-matcher:latest username/visual-matcher:latest
docker push username/visual-matcher:latest

# Deploy from Railway dashboard using Docker Hub image
```

**Option 2: GitHub**
```bash
# Push to GitHub
git push origin master

# Railway will auto-detect and deploy from Dockerfile
```

### Environment Variables

Required for production:
```env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
PORT=8080
```

## 📚 Documentation

For detailed deployment instructions, see:
- [Deployment Checklist](../docs/DEPLOYMENT_CHECKLIST.md)
- [API Documentation](../docs/API_DOCUMENTATION.md)

## ⚙️ Configuration

### Gunicorn (Production)
- Workers: 1 (CPU intensive ML app)
- Threads: 4
- Timeout: 300s (for ML processing)
- Port: 8080

### Docker Image
- Base: python:3.10-slim
- Size: ~12GB (includes PyTorch, CLIP model)
- Startup time: 10-30 seconds (model loading)

## 🔧 Troubleshooting

**Container won't start:**
- Check logs: `docker logs container-name`
- Verify environment variables
- Ensure PORT is 8080

**Out of memory:**
- Minimum: 2GB RAM
- Recommended: 4GB RAM
- Railway free tier may not be sufficient

**Slow responses:**
- Normal for first request (cold start)
- Subsequent requests faster (model cached)
