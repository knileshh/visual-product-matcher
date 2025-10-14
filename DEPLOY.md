# Deployment Scripts

## Quick Deploy to Render.com

```bash
# 1. Install Render CLI (optional)
npm install -g @render/cli

# 2. Login to Render
render login

# 3. Create render.yaml configuration
# (See render.yaml in root directory)

# 4. Deploy
render deploy
```

## Quick Deploy to Railway

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Initialize project
railway init

# 4. Deploy
railway up
```

## Manual Deployment Checklist

- [ ] Update `config.yaml` with production settings
- [ ] Set `app.debug: false`
- [ ] Set strong `app.secret_key`
- [ ] Configure `ml.device` based on available hardware
- [ ] Run `python init_data.py` to build index
- [ ] Verify all dependencies in `requirements.txt`
- [ ] Set environment variables on hosting platform
- [ ] Configure domain and SSL certificate
- [ ] Test health endpoint: `/api/health`
- [ ] Monitor logs for errors
- [ ] Set up backup strategy for database and index

## Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=<generate-strong-random-key>
ML_DEVICE=cpu
LOG_LEVEL=INFO
```

## Post-Deployment Testing

```bash
# Health check
curl https://your-domain.com/api/health

# Test upload (with local file)
curl -X POST https://your-domain.com/api/upload \
  -F "file=@test.jpg" \
  -F "k=10"

# Test URL search
curl -X POST https://your-domain.com/api/search-url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/image.jpg","k":10}'
```
