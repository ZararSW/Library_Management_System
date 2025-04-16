from datetime import datetime
from app import db
from flask_login import UserMixin

# Association table for many-to-many relationship between books and tags
book_tag_association = db.Table(
    'book_tag_association',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('book_tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reviews = db.relationship('BookReview', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Book(db.Model):
    """Book model for storing book details"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    status = db.Column(db.String(20), default='available')  # available, issued
    isbn = db.Column(db.String(20), unique=True)
    publication_year = db.Column(db.Integer)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    cover_thumbnail = db.Column(db.String(255))
    average_rating = db.Column(db.Float, default=0.0)
    total_ratings = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issued_records = db.relationship('IssuedBook', backref='book', lazy=True)
    reviews = db.relationship('BookReview', backref='book', lazy=True)
    reservations = db.relationship('BookReservation', backref='book', lazy=True)
    tags = db.relationship('BookTag', secondary=book_tag_association, backref=db.backref('books', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Book {self.title}>'

class Member(db.Model):
    """Member model for storing library members"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    membership_type = db.Column(db.String(20), default='standard')  # standard, premium
    membership_expiry = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    issued_books = db.relationship('IssuedBook', backref='member', lazy=True)
    reviews = db.relationship('BookReview', backref='member', lazy=True)
    reservations = db.relationship('BookReservation', backref='member', lazy=True)
    
    def __repr__(self):
        return f'<Member {self.name}>'

class IssuedBook(db.Model):
    """IssuedBook model for tracking book circulation"""
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    fine_amount = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<IssuedBook {self.id}>'

class BookReview(db.Model):
    """BookReview model for storing book reviews and ratings"""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BookReview {self.id}>'

class BookReservation(db.Model):
    """BookReservation model for tracking book reservations"""
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, fulfilled, cancelled
    notification_sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<BookReservation {self.id}>'

class BookTag(db.Model):
    """BookTag model for categorizing books"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    def __repr__(self):
        return f'<BookTag {self.name}>'
