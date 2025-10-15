"""
Setup configuration for Visual Product Matcher
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="visual-product-matcher",
    version="1.2.0",
    author="Nilesh Kumar",
    author_email="hey@knileshh.com",
    description="AI-powered visual search engine for finding similar fashion products",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/knileshh/visual-product-matcher",
    project_urls={
        "Bug Tracker": "https://github.com/knileshh/visual-product-matcher/issues",
        "Documentation": "https://github.com/knileshh/visual-product-matcher/blob/main/README.md",
        "Source Code": "https://github.com/knileshh/visual-product-matcher",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "flask>=3.0.0",
        "flask-cors>=4.0.0",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "clip @ git+https://github.com/openai/CLIP.git",
        "faiss-cpu>=1.7.4",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
        "SQLAlchemy>=2.0.0",
        "PyYAML>=6.0",
        "cloudinary>=1.36.0",
        "gunicorn>=21.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
        ],
    },
)
