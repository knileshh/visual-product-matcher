// Visual Product Matcher - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // File upload preview
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const fileLabel = document.querySelector('.file-label');

    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                previewContainer.style.display = 'block';
                fileLabel.querySelector('.file-text').textContent = fileInput.files[0].name;
            };
            
            reader.readAsDataURL(this.files[0]);
        }
    });

    // Drag and drop
    const fileDropArea = document.querySelector('.file-label');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => {
            fileDropArea.style.borderColor = '#667eea';
            fileDropArea.style.background = '#f0f4ff';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => {
            fileDropArea.style.borderColor = '#ccc';
            fileDropArea.style.background = '#fafafa';
        }, false);
    });

    fileDropArea.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            const event = new Event('change');
            fileInput.dispatchEvent(event);
        }
    }, false);

    // Threshold sliders
    const thresholdSlider = document.getElementById('similarity-threshold');
    const thresholdValue = document.getElementById('threshold-value');
    
    thresholdSlider.addEventListener('input', function() {
        thresholdValue.textContent = parseFloat(this.value).toFixed(2);
    });

    const urlThresholdSlider = document.getElementById('url-similarity-threshold');
    const urlThresholdValue = document.getElementById('url-threshold-value');
    
    urlThresholdSlider.addEventListener('input', function() {
        urlThresholdValue.textContent = parseFloat(this.value).toFixed(2);
    });

    // File upload form submission
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        const fileInput = document.getElementById('file-input');
        const k = document.getElementById('result-count').value;
        const threshold = document.getElementById('similarity-threshold').value;
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showError('Please select an image file');
            return;
        }
        
        formData.append('file', fileInput.files[0]);
        formData.append('k', k);
        formData.append('threshold', threshold);
        
        await performSearch('/api/upload', formData, false);
    });

    // URL form submission
    const urlForm = document.getElementById('url-form');
    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const url = document.getElementById('url-input').value;
        const k = document.getElementById('url-result-count').value;
        const threshold = document.getElementById('url-similarity-threshold').value;
        
        if (!url) {
            showError('Please enter an image URL');
            return;
        }
        
        const data = {
            url: url,
            k: parseInt(k),
            threshold: parseFloat(threshold)
        };
        
        await performSearch('/api/search-url', JSON.stringify(data), true);
    });

    // Perform search
    async function performSearch(endpoint, data, isJson) {
        const button = event.target.querySelector('.btn-primary');
        const btnText = button.querySelector('.btn-text');
        const btnLoader = button.querySelector('.btn-loader');
        const errorMessage = document.getElementById('error-message');
        
        // Show loading state
        button.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline';
        errorMessage.style.display = 'none';
        
        try {
            const options = {
                method: 'POST',
                body: data
            };
            
            if (isJson) {
                options.headers = {
                    'Content-Type': 'application/json'
                };
            }
            
            const response = await fetch(endpoint, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || 'Search failed');
            }
            
            // Display results
            displayResults(result);
            
        } catch (error) {
            console.error('Search error:', error);
            showError(error.message || 'An error occurred during search');
        } finally {
            // Reset button state
            button.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }

    // Display search results
    function displayResults(data) {
        const resultsSection = document.getElementById('results-section');
        const queryImage = document.getElementById('query-image');
        const resultsCount = document.getElementById('results-count');
        const resultsGrid = document.getElementById('results-grid');
        
        // Set query image
        if (data.query_image) {
            // Extract just the filename for the upload URL
            const filename = data.query_image.split(/[\\\/]/).pop();
            queryImage.src = `/uploads/${filename}`;
        } else if (data.query_url) {
            queryImage.src = data.query_url;
        }
        
        // Set results count
        resultsCount.textContent = data.results_count;
        
        // Clear previous results
        resultsGrid.innerHTML = '';
        
        // Add result cards
        if (data.products && data.products.length > 0) {
            data.products.forEach(product => {
                const card = createResultCard(product);
                resultsGrid.appendChild(card);
            });
        } else {
            resultsGrid.innerHTML = '<p style="text-align: center; width: 100%; padding: 2rem;">No similar products found. Try adjusting the similarity threshold.</p>';
        }
        
        // Show results section
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Create result card
    function createResultCard(product) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        // Get image path - handle both absolute and relative paths
        let imagePath = product.image_path;
        if (imagePath.includes('fashion-images')) {
            const parts = imagePath.split('fashion-images');
            imagePath = parts[parts.length - 1].replace(/\\/g, '/');
            if (imagePath.startsWith('/')) {
                imagePath = imagePath.substring(1);
            }
        }
        
        const similarityPercent = (product.similarity * 100).toFixed(1);
        
        card.innerHTML = `
            <img src="/products/${imagePath}" alt="${product.name}" loading="lazy" onerror="this.src='/static/images/placeholder.png'">
            <div class="result-info">
                <div class="result-name" title="${product.name}">${product.name}</div>
                <div class="result-category">${product.category || 'Fashion'}</div>
                <div class="result-similarity">${similarityPercent}% Match</div>
            </div>
        `;
        
        return card;
    }

    // Show error message
    function showError(message) {
        const errorMessage = document.getElementById('error-message');
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.style.display = 'none';
        }, 5000);
    }
});
