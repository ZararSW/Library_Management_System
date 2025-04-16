from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
from app import db
from models import Book, Member, IssuedBook, BookReservation
from forms import IssueBookForm, ReturnBookForm, BookReservationForm
from utils import calculate_fine, export_issued_books_to_csv
from datetime import datetime

circulation_bp = Blueprint('circulation', __name__, url_prefix='/circulation')

@circulation_bp.route('/issued', methods=['GET'])
@login_required
def issued_books():
    if not current_user.is_admin:
        abort(403)
    
    # Filter options
    status = request.args.get('status', 'all')
    member_id = request.args.get('member_id')
    
    query = IssuedBook.query
    
    if status == 'returned':
        query = query.filter(IssuedBook.return_date != None)
    elif status == 'not_returned':
        query = query.filter(IssuedBook.return_date == None)
    
    if member_id:
        query = query.filter_by(member_id=member_id)
    
    issued_books = query.order_by(IssuedBook.issue_date.desc()).all()
    
    # Get all members for filter dropdown
    members = Member.query.order_by(Member.name).all()
    
    return render_template('issued_books/list.html', 
                          title='Issued Books', 
                          issued_books=issued_books, 
                          status=status, 
                          selected_member_id=member_id if member_id else None,
                          members=members)

@circulation_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue_book():
    if not current_user.is_admin:
        abort(403)
    
    form = IssueBookForm()
    
    # Populate dropdown choices
    form.member_id.choices = [(m.id, m.name) for m in Member.query.order_by(Member.name).all()]
    
    # Only show available books
    available_books = Book.query.filter_by(status='available').order_by(Book.title).all()
    form.book_id.choices = [(b.id, f"{b.title} by {b.author}") for b in available_books]
    
    if form.validate_on_submit():
        book = Book.query.get(form.book_id.data)
        
        # Check if the book is available
        if book.status != 'available':
            flash('This book is not available for issue.', 'danger')
            return redirect(url_for('circulation.issue_book'))
        
        # Create the issued book record
        issued_book = IssuedBook(
            member_id=form.member_id.data,
            book_id=form.book_id.data,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data
        )
        
        # Update book status to issued
        book.status = 'issued'
        
        # Save to database
        db.session.add(issued_book)
        db.session.commit()
        
        flash('Book issued successfully!', 'success')
        return redirect(url_for('circulation.issued_books'))
    
    return render_template('issued_books/add.html', title='Issue Book', form=form)

@circulation_bp.route('/return/<int:issued_id>', methods=['GET', 'POST'])
@login_required
def return_book(issued_id):
    if not current_user.is_admin:
        abort(403)
    
    issued_book = IssuedBook.query.get_or_404(issued_id)
    
    # If already returned, redirect
    if issued_book.return_date:
        flash('This book has already been returned.', 'warning')
        return redirect(url_for('circulation.issued_books'))
    
    form = ReturnBookForm()
    form.issued_book_id.data = issued_id
    
    # Calculate fine based on selected return date
    if request.method == 'GET':
        fine_amount = calculate_fine(issued_book.due_date)
        form.fine_amount.data = fine_amount
    
    if form.validate_on_submit():
        issued_book.return_date = form.return_date.data
        issued_book.fine_amount = form.fine_amount.data
        
        # Update book status to available
        book = Book.query.get(issued_book.book_id)
        book.status = 'available'
        
        # Check for reservations
        reservation = BookReservation.query.filter_by(
            book_id=issued_book.book_id, 
            status='pending'
        ).order_by(BookReservation.reservation_date).first()
        
        if reservation:
            reservation.status = 'fulfilled'
            reservation.notification_sent = True
            flash(f'The book has been reserved by {reservation.member.name}. Please notify them.', 'info')
        
        db.session.commit()
        flash('Book returned successfully!', 'success')
        return redirect(url_for('circulation.issued_books'))
    
    return render_template('issued_books/return.html', 
                          title='Return Book', 
                          form=form, 
                          issued_book=issued_book)

@circulation_bp.route('/export/csv')
@login_required
def export_csv():
    if not current_user.is_admin:
        abort(403)
    
    csv_data = export_issued_books_to_csv()
    
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=issued_books.csv'}
    )
    
    return response

@circulation_bp.route('/reservations', methods=['GET'])
@login_required
def reservations():
    if not current_user.is_admin:
        abort(403)
    
    status = request.args.get('status', 'all')
    
    query = BookReservation.query
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    reservations = query.order_by(BookReservation.reservation_date.desc()).all()
    
    return render_template('reservations/list.html', 
                          title='Book Reservations', 
                          reservations=reservations, 
                          status=status)

@circulation_bp.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve_book():
    form = BookReservationForm()
    
    # Populate dropdown choices
    form.member_id.choices = [(m.id, m.name) for m in Member.query.order_by(Member.name).all()]
    
    # Only show issued books
    issued_books = Book.query.filter_by(status='issued').order_by(Book.title).all()
    form.book_id.choices = [(b.id, f"{b.title} by {b.author}") for b in issued_books]
    
    if form.validate_on_submit():
        # Check if already reserved by this member
        existing_reservation = BookReservation.query.filter_by(
            book_id=form.book_id.data,
            member_id=form.member_id.data,
            status='pending'
        ).first()
        
        if existing_reservation:
            flash('You have already reserved this book.', 'warning')
            return redirect(url_for('books.list'))
        
        # Create reservation
        reservation = BookReservation(
            book_id=form.book_id.data,
            member_id=form.member_id.data,
            reservation_date=datetime.utcnow(),
            status='pending'
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash('Book reserved successfully!', 'success')
        if current_user.is_admin:
            return redirect(url_for('circulation.reservations'))
        else:
            return redirect(url_for('books.list'))
    
    return render_template('reservations/add.html', title='Reserve Book', form=form)

@circulation_bp.route('/reservations/<int:reservation_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    reservation = BookReservation.query.get_or_404(reservation_id)
    
    # Check if the user has permission
    if not current_user.is_admin and current_user.id != reservation.member.user_id:
        abort(403)
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    flash('Reservation cancelled successfully!', 'success')
    
    if current_user.is_admin:
        return redirect(url_for('circulation.reservations'))
    else:
        return redirect(url_for('books.list'))
