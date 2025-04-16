from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from models import Member, IssuedBook
from forms import MemberForm
from datetime import datetime

members_bp = Blueprint('members', __name__, url_prefix='/members')

@members_bp.route('/', methods=['GET'])
@login_required
def list():
    if not current_user.is_admin:
        abort(403)
    
    search_term = request.args.get('search', '')
    
    if search_term:
        members = Member.query.filter(
            (Member.name.like(f'%{search_term}%')) | 
            (Member.email.like(f'%{search_term}%'))
        ).order_by(Member.name).all()
    else:
        members = Member.query.order_by(Member.name).all()
    
    return render_template('members/list.html', title='Members', members=members, search_term=search_term)

@members_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.is_admin:
        abort(403)
    
    form = MemberForm()
    
    if form.validate_on_submit():
        member = Member(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            membership_type=form.membership_type.data,
            membership_expiry=form.membership_expiry.data
        )
        
        db.session.add(member)
        db.session.commit()
        
        flash('Member added successfully!', 'success')
        return redirect(url_for('members.list'))
    
    return render_template('members/add.html', title='Add Member', form=form)

@members_bp.route('/<int:member_id>', methods=['GET'])
@login_required
def view(member_id):
    if not current_user.is_admin:
        abort(403)
    
    member = Member.query.get_or_404(member_id)
    
    # Get member's activity (issued books)
    issued_books = IssuedBook.query.filter_by(member_id=member_id).order_by(IssuedBook.issue_date.desc()).all()
    
    # Calculate stats
    total_books = len(issued_books)
    current_books = len([b for b in issued_books if not b.return_date])
    returned_books = len([b for b in issued_books if b.return_date])
    overdue_books = len([b for b in issued_books if not b.return_date and b.due_date < datetime.now().date()])
    total_fines = sum([b.fine_amount for b in issued_books if b.fine_amount])
    
    stats = {
        'total_books': total_books,
        'current_books': current_books,
        'returned_books': returned_books,
        'overdue_books': overdue_books,
        'total_fines': total_fines
    }
    
    return render_template('members/view.html', title='Member Details', member=member, issued_books=issued_books, stats=stats)

@members_bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(member_id):
    if not current_user.is_admin:
        abort(403)
    
    member = Member.query.get_or_404(member_id)
    form = MemberForm()
    
    # For GET request, populate form with member data
    if request.method == 'GET':
        form.name.data = member.name
        form.email.data = member.email
        form.phone.data = member.phone
        form.address.data = member.address
        form.membership_type.data = member.membership_type
        form.membership_expiry.data = member.membership_expiry
    
    if form.validate_on_submit():
        member.name = form.name.data
        member.email = form.email.data
        member.phone = form.phone.data
        member.address = form.address.data
        member.membership_type = form.membership_type.data
        member.membership_expiry = form.membership_expiry.data
        
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members.view', member_id=member.id))
    
    return render_template('members/edit.html', title='Edit Member', form=form, member=member)

@members_bp.route('/<int:member_id>/delete', methods=['POST'])
@login_required
def delete(member_id):
    if not current_user.is_admin:
        abort(403)
    
    member = Member.query.get_or_404(member_id)
    
    # Check if member has any issued books
    has_issued_books = IssuedBook.query.filter_by(member_id=member_id, return_date=None).first() is not None
    
    if has_issued_books:
        flash('Cannot delete member with issued books. Please return all books first.', 'danger')
        return redirect(url_for('members.view', member_id=member.id))
    
    db.session.delete(member)
    db.session.commit()
    
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('members.list'))
