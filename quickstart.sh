#!/bin/bash
# Quick Start Script for Visual Product Matcher

set -e

echo "=========================================="
echo "Visual Product Matcher - Quick Start"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate  # Windows Git Bash
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate  # Linux/Mac
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if data is initialized
if [ ! -f "data/products.db" ]; then
    echo ""
    echo "=========================================="
    echo "Data Not Initialized"
    echo "=========================================="
    echo "You need to run the data initialization script:"
    echo ""
    echo "  python init_data.py"
    echo ""
    echo "This will scan fashion-images/ and build the search index."
    echo "Estimated time: 30-60 minutes for 42K images"
    echo ""
    read -p "Run initialization now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python init_data.py
    else
        echo "Skipping initialization. Run 'python init_data.py' before starting the app."
        exit 0
    fi
fi

# Start the application
echo ""
echo "=========================================="
echo "Starting Visual Product Matcher"
echo "=========================================="
echo ""
echo "The application will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
