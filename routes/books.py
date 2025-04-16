from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from models import Book, BookTag, book_tag_association
from forms import BookForm, BookSearchForm, BookTagForm
from utils import save_image, create_thumbnail, generate_qr_code
import os
import base64
from io import BytesIO

books_bp = Blueprint('books', __name__, url_prefix='/books')

@books_bp.route('/', methods=['GET'])
def list():
    form = BookSearchForm()
    
    # Populate category choices
    categories = db.session.query(Book.category).distinct().all()
    form.category.choices = [('', 'All Categories')] + [(c[0], c[0]) for c in categories if c[0]]
    
    # Populate tag choices
    tags = BookTag.query.all()
    form.tag.choices = [('', 'All Tags')] + [(str(t.id), t.name) for t in tags]
    
    # Handle search and filters
    query = Book.query
    
    if request.args.get('search_term'):
        search_term = f"%{request.args.get('search_term')}%"
        query = query.filter(
            (Book.title.like(search_term)) | 
            (Book.author.like(search_term)) | 
            (Book.isbn.like(search_term))
        )
    
    if request.args.get('category') and request.args.get('category') != '':
        query = query.filter_by(category=request.args.get('category'))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter_by(status=request.args.get('status'))
    
    if request.args.get('tag') and request.args.get('tag') != '':
        tag_id = int(request.args.get('tag'))
        query = query.filter(Book.tags.any(id=tag_id))
    
    books = query.order_by(Book.title).all()
    
    return render_template('books/list.html', title='Books', books=books, form=form)

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = BookForm()
    
    # Populate tags dropdown
    tags = BookTag.query.all()
    form.tags.choices = [(t.id, t.name) for t in tags]
    
    if form.validate_on_submit():
        # Handle image upload
        cover_image = None
        cover_thumbnail = None
        
        if form.cover_image.data:
            cover_image = save_image(form.cover_image.data, 'ORIGINALS_FOLDER')
            cover_thumbnail = create_thumbnail(cover_image)
        
        book = Book(
            title=form.title.data,
            author=form.author.data,
            category=form.category.data,
            isbn=form.isbn.data,
            publication_year=form.publication_year.data,
            description=form.description.data,
            cover_image=cover_image,
            cover_thumbnail=cover_thumbnail,
            status='available'
        )
        
        # Add selected tags
        selected_tags = BookTag.query.filter(BookTag.id.in_(form.tags.data)).all()
        book.tags = selected_tags
        
        db.session.add(book)
        db.session.commit()
        
        flash('Book added successfully!', 'success')
        return redirect(url_for('books.list'))
    
    return render_template('books/add.html', title='Add Book', form=form)

@books_bp.route('/<int:book_id>', methods=['GET'])
def view(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books/view.html', title=book.title, book=book)

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(book_id):
    if not current_user.is_admin:
        abort(403)
    
    book = Book.query.get_or_404(book_id)
    form = BookForm()
    
    # Populate tags dropdown
    tags = BookTag.query.all()
    form.tags.choices = [(t.id, t.name) for t in tags]
    
    # For GET request, populate form with book data
    if request.method == 'GET':
        form.title.data = book.title
        form.author.data = book.author
        form.category.data = book.category
        form.isbn.data = book.isbn
        form.publication_year.data = book.publication_year
        form.description.data = book.description
        form.tags.data = [tag.id for tag in book.tags]
    
    if form.validate_on_submit():
        book.title = form.title.data
        book.author = form.author.data
        book.category = form.category.data
        book.isbn = form.isbn.data
        book.publication_year = form.publication_year.data
        book.description = form.description.data
        
        # Handle image upload
        if form.cover_image.data:
            # Delete old images if they exist
            if book.cover_image:
                try:
                    os.remove(os.path.join(current_app.config['ORIGINALS_FOLDER'], book.cover_image))
                except Exception as e:
                    current_app.logger.error(f"Error removing old cover image: {e}")
            
            if book.cover_thumbnail:
                try:
                    os.remove(os.path.join(current_app.config['THUMBNAILS_FOLDER'], book.cover_thumbnail))
                except Exception as e:
                    current_app.logger.error(f"Error removing old thumbnail: {e}")
            
            # Save new images
            book.cover_image = save_image(form.cover_image.data, 'ORIGINALS_FOLDER')
            book.cover_thumbnail = create_thumbnail(book.cover_image)
        
        # Update tags
        selected_tags = BookTag.query.filter(BookTag.id.in_(form.tags.data)).all()
        book.tags = selected_tags
        
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books.view', book_id=book.id))
    
    return render_template('books/edit.html', title='Edit Book', form=form, book=book)

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
def delete(book_id):
    if not current_user.is_admin:
        abort(403)
    
    book = Book.query.get_or_404(book_id)
    
    # Delete cover images if they exist
    if book.cover_image:
        try:
            os.remove(os.path.join(current_app.config['ORIGINALS_FOLDER'], book.cover_image))
        except Exception as e:
            current_app.logger.error(f"Error removing cover image: {e}")
    
    if book.cover_thumbnail:
        try:
            os.remove(os.path.join(current_app.config['THUMBNAILS_FOLDER'], book.cover_thumbnail))
        except Exception as e:
            current_app.logger.error(f"Error removing thumbnail: {e}")
    
    db.session.delete(book)
    db.session.commit()
    
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('books.list'))

@books_bp.route('/tags', methods=['GET', 'POST'])
@login_required
def tags():
    if not current_user.is_admin:
        abort(403)
    
    form = BookTagForm()
    tags = BookTag.query.order_by(BookTag.name).all()
    
    if form.validate_on_submit():
        tag = BookTag(name=form.name.data)
        db.session.add(tag)
        db.session.commit()
        flash('Tag added successfully!', 'success')
        return redirect(url_for('books.tags'))
    
    return render_template('books/tags.html', title='Book Tags', form=form, tags=tags)

@books_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    if not current_user.is_admin:
        abort(403)
    
    tag = BookTag.query.get_or_404(tag_id)
    db.session.delete(tag)
    db.session.commit()
    
    flash('Tag deleted successfully!', 'success')
    return redirect(url_for('books.tags'))

@books_bp.route('/<int:book_id>/qrcode', methods=['GET'])
@login_required
def get_qr_code(book_id):
    """Generate QR code for book checkout"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    book = Book.query.get_or_404(book_id)
    
    # Create QR code data with book info and checkout URL
    qr_data = {
        'id': book.id,
        'title': book.title,
        'isbn': book.isbn,
        'checkout_url': url_for('circulation.issue_book', book_id=book.id, _external=True)
    }
    
    # Generate QR code
    qr_img_io = generate_qr_code(str(qr_data))
    
    if not qr_img_io:
        return jsonify({'success': False, 'error': 'Failed to generate QR code'}), 500
    
    # Convert to base64 string
    qr_img_io.seek(0)
    img_str = base64.b64encode(qr_img_io.getvalue()).decode('utf-8')
    
    return jsonify({
        'success': True,
        'qr_code': img_str,
        'book': {
            'id': book.id,
            'title': book.title
        }
    })
