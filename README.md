# Visual Product Matcher

> AI-powered visual search engine for finding similar fashion products using CLIP embeddings and FAISS similarity search.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![CLIP](https://img.shields.io/badge/CLIP-OpenAI-orange.svg)](https://github.com/openai/CLIP)
[![FAISS](https://img.shields.io/badge/FAISS-Meta-red.svg)](https://github.com/facebookresearch/faiss)

## 🚀 Live Demo

[Coming Soon - Deployment URL will be added here]

## ✨ Features

- **Visual Search**: Upload an image or provide a URL to find visually similar products
- **AI-Powered**: Uses OpenAI's CLIP model for semantic image understanding
- **Fast Search**: FAISS indexing enables efficient similarity search across 42K+ products
- **Adjustable Threshold**: Fine-tune similarity matching with adjustable threshold slider
- **Responsive UI**: Mobile-friendly interface that works on all devices
- **RESTful API**: Well-documented API endpoints for integration

## 🏗️ Architecture

The application uses a modern ML stack:
- **CLIP (ViT-B/32)** for generating semantic image embeddings
- **FAISS** for efficient vector similarity search
- **Flask** for REST API and web serving
- **SQLite** for product metadata storage
- **Vanilla JS** for lightweight, fast frontend

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture information.

## 📋 Prerequisites

- Python 3.9 or higher
- CUDA-capable GPU (optional, but recommended for faster processing)
- 4GB+ RAM
- 2GB+ disk space for models and data

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

### 4. Initialize Data

Build the product database and FAISS index:

```bash
python init_data.py
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

### Running with Gunicorn (Production)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📚 API Documentation

See [docs/API.md](docs/API.md) for complete API documentation.

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
  -d '{"url": "https://example.com/image.jpg", "k": 10, "threshold": 0.3}'
```

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

## 🧪 Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## 📁 Project Structure

```
visual-product-matcher/
├── app.py                    # Flask application entry point
├── init_data.py              # Data initialization script
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── src/
│   ├── models.py            # Database models
│   ├── services/            # Business logic services
│   │   ├── embedding_service.py
│   │   ├── search_service.py
│   │   └── image_service.py
│   └── routes/              # API and UI routes
│       ├── api.py
│       └── ui.py
├── static/                  # Frontend assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/               # HTML templates
├── tests/                   # Test suite
├── data/                    # Data storage
│   ├── products.db         # SQLite database
│   ├── index/              # FAISS index
│   └── embeddings/         # Cached embeddings
├── fashion-images/          # Product images
└── docs/                    # Documentation
```

## 🎯 Configuration

Edit `config.yaml` to customize:
- ML model settings (CLIP variant, device)
- Search parameters (k, threshold)
- Upload limits and file formats
- Database and index paths

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/API.md) - API endpoints and examples
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [Approach](docs/APPROACH.md) - Technical approach and decisions

## 🔬 Technology Stack

- **Backend**: Python, Flask, Gunicorn
- **ML/AI**: PyTorch, CLIP, FAISS
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Testing**: pytest
- **Deployment**: [Platform TBD - Render/Railway/etc.]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for CLIP model
- Meta for FAISS library
- Fashion image dataset contributors

## 📞 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using CLIP and FAISS**
