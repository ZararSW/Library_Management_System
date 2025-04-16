import os
import csv
import io
from PIL import Image
from flask import current_app
from datetime import datetime, date
from werkzeug.utils import secure_filename
import uuid
from models import Book, Member, IssuedBook, BookReview

def save_image(file, folder):
    """Save an image to the specified folder and return the filename"""
    if not file:
        return None
        
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(current_app.config[folder], unique_filename)
    file.save(file_path)
    return unique_filename

def create_thumbnail(original_filename, size=(200, 300)):
    """Create a thumbnail for the given image file"""
    if not original_filename:
        return None
        
    original_path = os.path.join(current_app.config['ORIGINALS_FOLDER'], original_filename)
    thumbnail_filename = f"thumb_{original_filename}"
    thumbnail_path = os.path.join(current_app.config['THUMBNAILS_FOLDER'], thumbnail_filename)
    
    with Image.open(original_path) as img:
        img = img.convert('RGB')
        img.thumbnail(size)
        img.save(thumbnail_path)
    
    return thumbnail_filename

def calculate_fine(due_date, return_date=None, rate_per_day=1.0):
    """Calculate fine for overdue books"""
    if not return_date:
        return_date = date.today()
    
    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    if isinstance(return_date, str):
        return_date = datetime.strptime(return_date, '%Y-%m-%d').date()
    
    if return_date <= due_date:
        return 0.0
    
    days_overdue = (return_date - due_date).days
    return days_overdue * rate_per_day

def get_book_recommendations(member_id, limit=5):
    """Get book recommendations for a member based on history and ratings"""
    from app import db
    from sqlalchemy import func
    
    # Get the member's borrowed books
    borrowed_book_ids = db.session.query(IssuedBook.book_id).filter_by(member_id=member_id).all()
    borrowed_book_ids = [b[0] for b in borrowed_book_ids]
    
    # Get the categories of borrowed books
    borrowed_categories = db.session.query(Book.category).filter(Book.id.in_(borrowed_book_ids)).distinct().all()
    borrowed_categories = [c[0] for c in borrowed_categories]
    
    # Find available books in same categories but not borrowed by the member
    recommendations = Book.query.filter(
        Book.category.in_(borrowed_categories),
        Book.status == 'available',
        ~Book.id.in_(borrowed_book_ids)
    ).order_by(Book.average_rating.desc()).limit(limit).all()
    
    # If we don't have enough recommendations, add some popular books
    if len(recommendations) < limit:
        popular_books = Book.query.filter(
            Book.status == 'available',
            ~Book.id.in_(borrowed_book_ids),
            ~Book.id.in_([b.id for b in recommendations])
        ).order_by(Book.average_rating.desc()).limit(limit - len(recommendations)).all()
        
        recommendations.extend(popular_books)
    
    return recommendations

def export_issued_books_to_csv():
    """Export issued books data to CSV"""
    issued_books = IssuedBook.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Member Name', 'Book Title', 'Issue Date', 'Due Date', 'Return Date', 'Fine Amount'])
    
    # Write data
    for record in issued_books:
        writer.writerow([
            record.id,
            record.member.name,
            record.book.title,
            record.issue_date,
            record.due_date,
            record.return_date,
            record.fine_amount
        ])
    
    return output.getvalue()

def update_book_rating(book_id):
    """Update the average rating for a book"""
    from app import db
    from sqlalchemy import func
    
    # Calculate average rating
    avg_rating = db.session.query(func.avg(BookReview.rating)).filter_by(book_id=book_id).scalar() or 0
    total_ratings = db.session.query(func.count(BookReview.rating)).filter_by(book_id=book_id).scalar() or 0
    
    # Update book
    book = Book.query.get(book_id)
    if book:
        book.average_rating = float(avg_rating)
        book.total_ratings = total_ratings
        db.session.commit()
