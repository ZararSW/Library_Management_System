from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from app import db
from models import Book, Member, IssuedBook, BookReview
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    if not current_user.is_admin:
        abort(403)
    
    # Key statistics
    total_books = Book.query.count()
    total_members = Member.query.count()
    total_issued = IssuedBook.query.filter(IssuedBook.return_date == None).count()
    total_overdue = IssuedBook.query.filter(
        IssuedBook.return_date == None,
        IssuedBook.due_date < datetime.now().date()
    ).count()
    
    # Category distribution
    category_data = db.session.query(
        Book.category, func.count(Book.id)
    ).group_by(Book.category).all()
    
    categories = [c[0] for c in category_data]
    category_counts = [c[1] for c in category_data]
    
    # Popular books (most borrowed)
    popular_books = db.session.query(
        Book,
        func.count(IssuedBook.id).label('issue_count')
    ).join(IssuedBook).group_by(Book.id).order_by(
        func.count(IssuedBook.id).desc()
    ).limit(5).all()
    
    # Recent issues
    recent_issues = IssuedBook.query.order_by(
        IssuedBook.issue_date.desc()
    ).limit(5).all()
    
    # Overdue books
    overdue_books = IssuedBook.query.filter(
        IssuedBook.return_date == None,
        IssuedBook.due_date < datetime.now().date()
    ).order_by(IssuedBook.due_date).all()
    
    # Member activity (most active members)
    active_members = db.session.query(
        Member,
        func.count(IssuedBook.id).label('issue_count')
    ).join(IssuedBook).group_by(Member.id).order_by(
        func.count(IssuedBook.id).desc()
    ).limit(5).all()
    
    # Monthly issue trend
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    
    # Use PostgreSQL compatible date formatting
    monthly_issues = db.session.query(
        func.to_char(IssuedBook.issue_date, 'YYYY-MM').label('month'),
        func.count(IssuedBook.id)
    ).filter(IssuedBook.issue_date >= six_months_ago).group_by('month').all()
    
    months = [m[0] for m in monthly_issues]
    issue_counts = [m[1] for m in monthly_issues]
    
    # Ratings distribution
    ratings_dist = db.session.query(
        BookReview.rating,
        func.count(BookReview.id)
    ).group_by(BookReview.rating).all()
    
    rating_values = [r[0] for r in ratings_dist]
    rating_counts = [r[1] for r in ratings_dist]
    
    return render_template(
        'dashboard.html',
        title='Dashboard',
        stats={
            'total_books': total_books,
            'total_members': total_members,
            'total_issued': total_issued,
            'total_overdue': total_overdue
        },
        category_data={
            'labels': categories,
            'data': category_counts
        },
        popular_books=popular_books,
        recent_issues=recent_issues,
        overdue_books=overdue_books,
        active_members=active_members,
        monthly_data={
            'labels': months,
            'data': issue_counts
        },
        ratings_data={
            'labels': rating_values,
            'data': rating_counts
        }
    )
