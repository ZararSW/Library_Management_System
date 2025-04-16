from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FloatField, DateField, HiddenField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from models import User, Book, Member, BookTag
from datetime import date, datetime, timedelta

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class CreateAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create Admin')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Profile')

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    author = StringField('Author', validators=[DataRequired(), Length(max=100)])
    category = StringField('Category', validators=[DataRequired(), Length(max=50)])
    isbn = StringField('ISBN', validators=[DataRequired(), Length(max=20)])
    publication_year = IntegerField('Publication Year', validators=[DataRequired(), NumberRange(min=1000, max=datetime.now().year)])
    description = TextAreaField('Description', validators=[DataRequired()])
    cover_image = FileField('Cover Image', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    tags = SelectMultipleField('Tags', coerce=int)
    submit = SubmitField('Submit')
    
    def validate_isbn(self, isbn):
        book = Book.query.filter_by(isbn=isbn.data).first()
        if book and (not hasattr(self, 'book_id') or book.id != self.book_id.data):
            raise ValidationError('ISBN already exists. Please use a different one.')

class BookSearchForm(FlaskForm):
    search_term = StringField('Search', validators=[Optional()])
    category = SelectField('Category', validators=[Optional()], choices=[('', 'All Categories')])
    status = SelectField('Status', validators=[Optional()], 
                         choices=[('', 'All Status'), ('available', 'Available'), ('issued', 'Issued')])
    tag = SelectField('Tag', validators=[Optional()], choices=[('', 'All Tags')])
    submit = SubmitField('Search')

class MemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    address = TextAreaField('Address', validators=[DataRequired()])
    membership_type = SelectField('Membership Type', choices=[('standard', 'Standard'), ('premium', 'Premium')])
    membership_expiry = DateField('Membership Expiry', validators=[DataRequired()], default=lambda: date.today() + timedelta(days=365))
    submit = SubmitField('Submit')
    
    def validate_email(self, email):
        member = Member.query.filter_by(email=email.data).first()
        if member and (not hasattr(self, 'member_id') or member.id != self.member_id.data):
            raise ValidationError('Email already registered. Please use a different one.')

class IssueBookForm(FlaskForm):
    member_id = SelectField('Member', validators=[DataRequired()], coerce=int)
    book_id = SelectField('Book', validators=[DataRequired()], coerce=int)
    issue_date = DateField('Issue Date', validators=[DataRequired()], default=date.today)
    due_date = DateField('Due Date', validators=[DataRequired()], default=lambda: date.today() + timedelta(days=14))
    submit = SubmitField('Issue Book')
    
    def validate_book_id(self, book_id):
        book = Book.query.get(book_id.data)
        if not book:
            raise ValidationError('Book not found.')
        if book.status != 'available':
            raise ValidationError('This book is not available for issue.')

class ReturnBookForm(FlaskForm):
    issued_book_id = HiddenField('Issued Book ID', validators=[DataRequired()])
    return_date = DateField('Return Date', validators=[DataRequired()], default=date.today)
    fine_amount = FloatField('Fine Amount', default=0.0)
    submit = SubmitField('Return Book')

class BookReservationForm(FlaskForm):
    member_id = SelectField('Member', validators=[DataRequired()], coerce=int)
    book_id = SelectField('Book', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Reserve Book')

class BookReviewForm(FlaskForm):
    rating = SelectField('Rating', validators=[DataRequired()], choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], coerce=int)
    review_text = TextAreaField('Review', validators=[Optional()])
    submit = SubmitField('Submit Review')

class BookTagForm(FlaskForm):
    name = StringField('Tag Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Add Tag')
    
    def validate_name(self, name):
        tag = BookTag.query.filter_by(name=name.data).first()
        if tag:
            raise ValidationError('Tag already exists.')
