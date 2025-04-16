from flask import render_template
from app import app

def index_page():
    """Render the home page"""
    return render_template('index.html', title='Home')
