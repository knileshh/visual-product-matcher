"""
UI routes for Visual Product Matcher.
"""
import logging
from flask import Blueprint, render_template, send_from_directory
import os

logger = logging.getLogger(__name__)

ui_bp = Blueprint('ui', __name__)


def init_ui(config):
    """
    Initialize UI routes.
    
    Args:
        config: Configuration dictionary
    """
    
    @ui_bp.route('/')
    def index():
        """Main application page."""
        return render_template('index.html')
    
    @ui_bp.route('/results')
    def results():
        """Results page."""
        return render_template('results.html')
    
    @ui_bp.route('/products/<path:filename>')
    def serve_product_image(filename):
        """Serve product images."""
        images_directory = config['products']['images_directory']
        return send_from_directory(images_directory, filename)
    
    @ui_bp.route('/uploads/<path:filename>')
    def serve_upload_image(filename):
        """Serve uploaded images."""
        upload_folder = config['upload']['upload_folder']
        return send_from_directory(upload_folder, filename)
    
    return ui_bp
