import os
import csv
import io
from PIL import Image
from flask import current_app
from datetime import datetime, date
from werkzeug.utils import secure_filename
import uuid
from models import Book, Member, IssuedBook, BookReview

def save_image(file, folder, allowed_extensions=None):
    """
    Save an image to the specified folder and return the filename
    
    Args:
        file: The uploaded file object
        folder: The folder configuration key (e.g., 'ORIGINALS_FOLDER')
        allowed_extensions: List of allowed file extensions
        
    Returns:
        str: The unique filename of the saved image or None if failed
    """
    if not file:
        return None
    
    if not allowed_extensions:
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower().replace('.', '')
    if file_ext not in allowed_extensions:
        current_app.logger.warning(f"Invalid file extension: {file_ext}")
        return None
    
    try:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config[folder], unique_filename)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the file
        file.save(file_path)
        
        # Validate that it's a real image
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image
            
        return unique_filename
    except Exception as e:
        current_app.logger.error(f"Error saving image: {str(e)}")
        # If anything goes wrong, clean up any partial file
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        return None

def create_thumbnail(original_filename, size=(200, 300)):
    """
    Create a thumbnail for the given image file
    
    Args:
        original_filename: The filename of the original image
        size: Thumbnail dimensions as (width, height) tuple
        
    Returns:
        str: The filename of the thumbnail or None if failed
    """
    if not original_filename:
        return None
    
    try:
        original_path = os.path.join(current_app.config['ORIGINALS_FOLDER'], original_filename)
        thumbnail_filename = f"thumb_{original_filename}"
        thumbnail_path = os.path.join(current_app.config['THUMBNAILS_FOLDER'], thumbnail_filename)
        
        # Ensure the thumbnail directory exists
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        with Image.open(original_path) as img:
            img = img.convert('RGB')
            
            # Calculate dimensions preserving aspect ratio
            img_width, img_height = img.size
            ratio = min(size[0] / img_width, size[1] / img_height)
            new_size = (int(img_width * ratio), int(img_height * ratio))
            
            # Resize and crop to fit exactly
            img = img.resize(new_size, Image.LANCZOS)
            
            # Create new image with exact dimensions
            new_img = Image.new("RGB", size, color="white")
            
            # Paste resized image centered on white background
            paste_x = (size[0] - new_size[0]) // 2
            paste_y = (size[1] - new_size[1]) // 2
            new_img.paste(img, (paste_x, paste_y))
            
            # Save the thumbnail
            new_img.save(thumbnail_path, quality=90)
        
        return thumbnail_filename
    except Exception as e:
        current_app.logger.error(f"Error creating thumbnail: {str(e)}")
        return None

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
        
def generate_qr_code(data, size=200, file_path=None):
    """
    Generate a QR code for the given data
    
    Args:
        data: The data to encode in the QR code
        size: The size of the QR code in pixels
        file_path: Optional path to save the QR code
        
    Returns:
        BytesIO object containing the QR code image, or True if saved to file_path
    """
    try:
        import qrcode
        from io import BytesIO
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        if file_path:
            img.save(file_path)
            return True
        else:
            bio = BytesIO()
            img.save(bio)
            bio.seek(0)
            return bio
    except ImportError:
        current_app.logger.error("qrcode library not installed")
        return None
    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {str(e)}")
        return None
        
def get_member_stats(member_id):
    """
    Get comprehensive statistics for a member
    
    Args:
        member_id: The ID of the member
        
    Returns:
        dict: A dictionary of member statistics
    """
    from app import db
    from sqlalchemy import func
    from datetime import datetime
    
    try:
        # Current date for calculations
        today = datetime.now().date()
        
        # Get basic counts
        total_books = db.session.query(func.count(IssuedBook.id)).filter_by(member_id=member_id).scalar() or 0
        current_books = db.session.query(func.count(IssuedBook.id)).filter_by(
            member_id=member_id, return_date=None).scalar() or 0
        overdue_books = db.session.query(func.count(IssuedBook.id)).filter(
            IssuedBook.member_id == member_id,
            IssuedBook.return_date == None,
            IssuedBook.due_date < today
        ).scalar() or 0
        
        # Calculate total fines
        total_fines = db.session.query(func.sum(IssuedBook.fine_amount)).filter_by(
            member_id=member_id).scalar() or 0
            
        # Get favorite categories
        favorite_categories = db.session.query(
            Book.category, func.count(IssuedBook.id).label('count')
        ).join(IssuedBook, IssuedBook.book_id == Book.id
        ).filter(IssuedBook.member_id == member_id
        ).group_by(Book.category
        ).order_by(func.count(IssuedBook.id).desc()
        ).limit(3).all()
        
        # Get reading frequency by month
        monthly_reading = db.session.query(
            func.to_char(IssuedBook.issue_date, 'YYYY-MM').label('month'),
            func.count(IssuedBook.id)
        ).filter(IssuedBook.member_id == member_id
        ).group_by('month'
        ).order_by('month').all()
        
        # Calculate reading velocity (avg days to finish a book)
        completed_books = db.session.query(
            func.avg(func.extract('day', IssuedBook.return_date) - func.extract('day', IssuedBook.issue_date))
        ).filter(
            IssuedBook.member_id == member_id,
            IssuedBook.return_date != None
        ).scalar() or 0
        
        return {
            'total_books': total_books,
            'current_books': current_books,
            'overdue_books': overdue_books,
            'total_fines': total_fines,
            'favorite_categories': favorite_categories,
            'monthly_reading': monthly_reading,
            'avg_reading_days': round(completed_books, 1)
        }
    except Exception as e:
        current_app.logger.error(f"Error getting member stats: {str(e)}")
        return {
            'total_books': 0,
            'current_books': 0,
            'overdue_books': 0,
            'total_fines': 0,
            'favorite_categories': [],
            'monthly_reading': [],
            'avg_reading_days': 0
        }
