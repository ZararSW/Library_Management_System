from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from models import Book, Member, BookReview
from forms import BookReviewForm
from utils import update_book_rating, get_book_recommendations

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@reviews_bp.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if user has already reviewed this book
    existing_review = BookReview.query.filter_by(
        book_id=book_id,
        user_id=current_user.id
    ).first()
    
    form = BookReviewForm()
    
    if existing_review and request.method == 'GET':
        form.rating.data = existing_review.rating
        form.review_text.data = existing_review.review_text
    
    if form.validate_on_submit():
        if existing_review:
            # Update existing review
            existing_review.rating = form.rating.data
            existing_review.review_text = form.review_text.data
            flash('Your review has been updated!', 'success')
        else:
            # Create new review
            # For simplicity, we'll create a dummy member ID for regular users who aren't members
            member = Member.query.filter_by(email=current_user.email).first()
            member_id = member.id if member else 1  # Default to first member if not found
            
            review = BookReview(
                book_id=book_id,
                member_id=member_id,
                user_id=current_user.id,
                rating=form.rating.data,
                review_text=form.review_text.data
            )
            db.session.add(review)
            flash('Your review has been submitted!', 'success')
        
        db.session.commit()
        update_book_rating(book_id)
        return redirect(url_for('books.view', book_id=book_id))
    
    return render_template('reviews/add.html', title='Add Review', form=form, book=book)

@reviews_bp.route('/book/<int:book_id>/delete', methods=['POST'])
@login_required
def delete_review(book_id):
    review = BookReview.query.filter_by(book_id=book_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(review)
    db.session.commit()
    update_book_rating(book_id)
    
    flash('Your review has been deleted!', 'success')
    return redirect(url_for('books.view', book_id=book_id))

@reviews_bp.route('/recommendations')
@login_required
def recommendations():
    # Find member ID for current user
    member = Member.query.filter_by(email=current_user.email).first()
    
    if not member:
        flash('You need a library membership to get personalized recommendations.', 'info')
        # Get generally popular books instead
        recommendations = Book.query.filter_by(status='available').order_by(Book.average_rating.desc()).limit(5).all()
    else:
        recommendations = get_book_recommendations(member.id)
    
    return render_template('recommendations.html', title='Book Recommendations', books=recommendations)
