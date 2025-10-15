# Visual Product Matcher

[Live Deployment](https://visualmatch.knileshh.com) 
[Frontend Repository](https://github.com/knileshh/visual-product-matcher-fe.git)

> 🎯 **Production-ready** AI-powered visual search engine with **42,700+ fashion products**. Find visually similar items using CLIP embeddings and FAISS similarity search.

**Created by [Nilesh Kumar](https://knileshh.com)** | [hey@knileshh.com](mailto:hey@knileshh.com)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![CLIP](https://img.shields.io/badge/CLIP-OpenAI-orange.svg)](https://github.com/openai/CLIP)
[![FAISS](https://img.shields.io/badge/FAISS-Meta-red.svg)](https://github.com/facebookresearch/faiss)
[![Docker](https://img.shields.io/badge/Docker-1.62GB-blue.svg)](https://hub.docker.com)
[![Products](https://img.shields.io/badge/Products-42.7K-green.svg)](#)

## 🌟 Highlights

- 🎨 **42,700+ Product Database** - Fully indexed fashion products with embeddings
- 🚀 **Production Ready** - Deployed with Docker (1.62GB optimized image)
- ⚡ **Lightning Fast** - <100ms search across entire catalog using FAISS
- 🤖 **AI-Powered** - OpenAI CLIP (ViT-B/32) for semantic understanding
- 🌐 **Cloud-Ready** - Cloudinary CDN integration for scalable storage
- 🔒 **Enterprise Security** - Rate limiting, validation, auto-cleanup
- 📊 **Real-Time Search** - Upload image or URL, get instant similar products
 - 🌍 **Live Demo** - Check the live deployment at https://visualmatch.knileshh.com

## � Project Scale

```
📦 Products:        42,700 fashion items
🔍 Embeddings:      21.8 million dimensions (42,700 × 512)
💾 Database:        187 MB optimized SQLite
🐳 Docker Image:    1.62 GB (87% optimized from 12.4GB)
⚡ Search Index:    FAISS IndexFlat for maximum accuracy
🌐 Image Storage:   Cloudinary CDN (globally distributed)
🎯 Search Speed:    <100ms for entire catalog
📊 Memory Usage:    ~1.5GB runtime
```

## �🚀 Features

- **Visual Search**: Upload an image or provide a URL to find visually similar products
- **AI-Powered**: Uses OpenAI's CLIP model for semantic image understanding
- **Fast Search**: FAISS indexing enables efficient similarity search across 42K+ products
 - **Try it Live**: Visit the live demo: https://visualmatch.knileshh.com
- **Adjustable Threshold**: Fine-tune similarity matching with adjustable threshold slider
- **Responsive UI**: Mobile-friendly interface that works on all devices
- **RESTful API**: Well-documented API endpoints for integration
- **Auto-Cleanup**: Automatic removal of old uploaded files to prevent storage bloat
- **Cloud Storage**: Integrated with Cloudinary for scalable image hosting

## 📁 Project Structure

```
visual-product-matcher/
├── app.py                      # Main Flask application
├── config.yaml                 # Application configuration
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── src/                       # Source code
│   ├── models/                # Database models
│   ├── services/              # Business logic services
│   ├── routes/                # API and UI routes
│   └── middleware/            # Security and rate limiting
│
├── templates/                 # HTML templates
├── static/                    # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
│
├── data/                      # Data directory (gitignored)
│   ├── products.db           # SQLite database
│   ├── embeddings/           # Cached embeddings
│   ├── index/                # FAISS index
│   ├── uploads/              # User uploads (auto-cleaned)
│   └── temp/                 # Temporary files
│
├── scripts/                   # Utility scripts
│   ├── init_data.py          # Initialize database and index
│   ├── upload_to_cloudinary.py  # Cloudinary migration
│   ├── quick_api_test.py     # API testing
│   └── README.md             # Scripts documentation
│
├── deployment/                # Deployment files
│   ├── Dockerfile            # Docker container
│   ├── gunicorn_config_cloud.py  # Production config
│   └── README.md             # Deployment guide
│
├── docs/                      # Documentation
│   ├── API_DOCUMENTATION.md  # API reference
│   ├── DEPLOYMENT_CHECKLIST.md  # Deployment guide
│   └── README.md             # Docs index
│
└── logs/                      # Application logs (gitignored)
```

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd visual-product-matcher
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# Add CLOUDINARY_URL if using Cloudinary
```

### 5. Initialize Data

Build the product database and FAISS index:

```bash
python scripts/init_data.py
```

This will:
- Scan all images in `fashion-images/` directory
- Extract metadata and store in SQLite database
- Generate CLIP embeddings for all products
- Build FAISS search index

**Note**: Initial setup may take 30-60 minutes for 42K images depending on your hardware.

## 🚀 Usage

### Running Locally

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Running with Docker

```bash
# Build image
docker build -t visual-matcher .

# Run container
docker run -d -p 8080:8080 --env-file .env visual-matcher

# Check health
curl http://localhost:8080/api/health
```

### Running in Production

```bash
gunicorn --config gunicorn_config_cloud.py "app:create_app()"
```

## 📚 Documentation

- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference for integration
- **[Deployment Guide](docs/DEPLOYMENT_CHECKLIST.md)** - Step-by-step deployment to Railway & Vercel
- **[Scripts Documentation](scripts/README.md)** - Utility scripts usage
- **[Deployment Files](deployment/README.md)** - Docker and production configuration

### Quick API Examples

**Upload and Search:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@image.jpg" \
  -F "k=10" \
  -F "threshold=0.3"
```

**Search by URL:**
```bash
curl -X POST http://localhost:5000/api/search-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg", "k": 10}'
```

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

## 🧪 Testing

Run API tests:

```bash
# Quick test (while server is running)
python scripts/quick_api_test.py

# Comprehensive test suite
python scripts/test_api_endpoints.py
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- **Upload settings**: File size limits, allowed formats, auto-cleanup intervals
- **ML settings**: CLIP model, device (CPU/GPU), batch size
- **Search settings**: Default results count, similarity thresholds
- **Performance**: Caching, indexing options

### Auto-Cleanup Feature

Uploaded files are automatically deleted after 60 minutes (configurable):

```yaml
upload:
  cleanup:
    enabled: true
    interval_minutes: 30  # Check every 30 minutes
    max_age_minutes: 60   # Delete files older than 60 minutes
```

## 🚢 Deployment

### Docker (Optimized: 1.62GB)

The Docker image has been optimized from 12.4GB to 1.62GB (87% reduction):

```bash
# Build optimized image
docker build -t visual-product-matcher:latest .

# Run locally
docker run -d -p 8080:8080 --env-file .env visual-product-matcher:latest

# Test
curl http://localhost:8080/api/health
```

### Push to Docker Hub

```bash
# Login
docker login

# Tag image
docker tag visual-product-matcher:latest YOUR_USERNAME/visual-product-matcher:latest
docker tag visual-product-matcher:latest YOUR_USERNAME/visual-product-matcher:v1.2.0

# Push
docker push YOUR_USERNAME/visual-product-matcher:latest
docker push YOUR_USERNAME/visual-product-matcher:v1.2.0
```

See [docs/DOCKER_HUB_PUSH.md](docs/DOCKER_HUB_PUSH.md) for detailed instructions.

### Railway Deployment

1. **From Docker Hub:**
   - Deploy: `YOUR_USERNAME/visual-product-matcher:latest`
   - Add environment variables
   - Set `PORT=8080`

2. **From GitHub:**
   - Connect your repository
   - Railway auto-detects Dockerfile
   - Configure environment variables
   - Deploy!

See [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) for complete guide.

### Next.js Frontend Integration

```typescript
// See docs/API_DOCUMENTATION.md for integration examples
const results = await fetch('https://your-api.railway.app/api/search-url', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ url: imageUrl, k: 20, threshold: 0.3 })
});
```

## 🔐 Security

- **Rate Limiting**: Upload (10/min), Search (30/min), General (100/hour)
- **File Validation**: Type, size, and integrity checks
- **SSRF Protection**: URL validation and sanitization
- **Auto-Cleanup**: Prevents storage exhaustion
- **CORS**: Configured for cross-origin requests

See [SECURITY.md](SECURITY.md) for security policy and reporting.

## 📊 Performance

- **Docker Image**: 1.62GB (optimized, 87% smaller than original 12.4GB)
- **Search Speed**: <100ms for 42K products (with FAISS)
- **Embedding Generation**: ~50ms per image (GPU) / ~200ms (CPU)
- **Memory Usage**: ~1.5GB runtime (with model loaded)
- **Database**: 187MB (SQLite with products + metadata)
- **Startup Time**: ~30 seconds (includes model loading)

## 🔬 Technology Stack

- **Backend**: Python 3.10, Flask 3.0, Gunicorn
- **ML/AI**: PyTorch (CPU-optimized), OpenAI CLIP (ViT-B/32), FAISS
- **Database**: SQLite with SQLAlchemy
- **Cloud Storage**: Cloudinary CDN
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Container**: Docker (multi-stage, optimized build)
- **Deployment**: Railway-ready, Cloud Run compatible

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Copyright (c) 2025 Nilesh Kumar**

## 🙏 Acknowledgments

- [OpenAI CLIP](https://github.com/openai/CLIP) - Vision and language model
- [Meta FAISS](https://github.com/facebookresearch/faiss) - Similarity search library
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Cloudinary](https://cloudinary.com/) - Image hosting and CDN

## 👨‍💻 Author

**Nilesh Kumar**
- Website: [knileshh.com](https://knileshh.com)
- Email: [hey@knileshh.com](mailto:hey@knileshh.com)
- GitHub: [@knileshh](https://github.com/knileshh)

---

**Built with ❤️ by Nilesh Kumar** • **Production Ready** 🚀


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [OpenAI CLIP](https://github.com/openai/CLIP) - Vision and language model
- [FAISS](https://github.com/facebookresearch/faiss) - Similarity search library
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Cloudinary](https://cloudinary.com/) - Image hosting platform

---

**Built with ❤️ by Nilesh Kumar** • **Production Ready** 🚀
