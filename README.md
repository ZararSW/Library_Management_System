# Library Management System

**A comprehensive web application for managing library operations including user authentication, book cataloging, circulation workflows, and analytics.**

## Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

## Features
- **User Management**: Role-based authentication (admin & member) with Flask-Login and WTForms.  
- **Book Management**: CRUD operations for books, cover image uploads, and QR code generation.  
- **Member Management**: Profile, membership tiers, loan history, and fine tracking.  
- **Circulation**: Issue/return workflows, due-date reminders, and automated fine calculation.  
- **Reviews & Ratings**: Member-submitted reviews with admin moderation and recommendation engine.  
- **Dashboard Analytics**: Interactive charts (Chart.js) for book categories, circulation stats, and fines.  

## Technology Stack
- **Backend:** Python 3.x, Flask, SQLAlchemy, Flask-Login, WTForms  
- **Frontend:** HTML5, Bootstrap 5, JavaScript, jQuery, Chart.js  
- **Database:** SQLite (development), PostgreSQL (production)  
- **Deployment:** Replit with Gunicorn  

## Project Structure
Library_Management_System/ ├── app.py # Flask app factory and config ├── main.py # Application entry point ├── models.py # Database models (SQLAlchemy) ├── forms.py # WTForms form definitions ├── utils.py # Utility functions (QR codes, email) ├── populate_books.py # Sample data seeding script ├── routes/ # Blueprint modules for each feature ├── templates/ # Jinja2 HTML templates ├── static/ # Static assets (css, js, images, uploads) ├── .replit # Replit configuration ├── replit.nix # Environment specification └── pyproject.toml # Project metadata and dependencies
