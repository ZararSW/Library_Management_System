#!/usr/bin/env python3
"""
Script to populate the library database with sample books.
This script adds a variety of books from different genres to get started.
"""

import os
import random
from datetime import datetime
from app import app, db
from models import Book, BookTag, book_tag_association, User
from werkzeug.security import generate_password_hash

# Define tags
TAGS = [
    "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery", 
    "Thriller", "Romance", "Historical", "Biography", "Self-Help",
    "Business", "Philosophy", "Science", "Technology", "Arts", 
    "Children", "Young Adult", "Classic", "Poetry", "Reference"
]

# Define categories
CATEGORIES = [
    "Fiction", "Non-Fiction", "Science Fiction", "Fantasy", "Mystery",
    "Thriller", "Romance", "Historical Fiction", "Biography", "Self-Help",
    "Business", "Philosophy", "Science", "Technology", "Arts & Music",
    "Children's Books", "Young Adult", "Classic Literature", "Poetry", "Reference"
]

# Sample books with real data
BOOKS = [
    {
        "title": "To Kill a Mockingbird",
        "author": "Harper Lee",
        "category": "Fiction",
        "isbn": "9780060935467",
        "publication_year": 1960,
        "description": "Set in the American South during the 1930s, the story of a lawyer who defends a Black man falsely accused of rape, as seen through the eyes of the lawyer's young daughter. A powerful exploration of racial injustice and moral growth.",
        "tags": ["Fiction", "Classic", "Historical"]
    },
    {
        "title": "1984",
        "author": "George Orwell",
        "category": "Fiction",
        "isbn": "9780451524935",
        "publication_year": 1949,
        "description": "A dystopian novel set in a totalitarian society ruled by the Party, which has total control over every aspect of people's lives. It explores themes of mass surveillance, repressive regimentation, and the manipulation of truth.",
        "tags": ["Fiction", "Classic", "Science Fiction"]
    },
    {
        "title": "The Great Gatsby",
        "author": "F. Scott Fitzgerald",
        "category": "Fiction",
        "isbn": "9780743273565",
        "publication_year": 1925,
        "description": "Set in the Jazz Age on Long Island, the novel depicts first-person narrator Nick Carraway's interactions with mysterious millionaire Jay Gatsby and Gatsby's obsession to reunite with his former lover, Daisy Buchanan.",
        "tags": ["Fiction", "Classic", "Romance"]
    },
    {
        "title": "Pride and Prejudice",
        "author": "Jane Austen",
        "category": "Romance",
        "isbn": "9780141439518",
        "publication_year": 1813,
        "description": "The story follows Elizabeth Bennet as she deals with issues of manners, upbringing, morality, education, and marriage in the society of the landed gentry of the British Regency.",
        "tags": ["Fiction", "Classic", "Romance"]
    },
    {
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "category": "Fantasy",
        "isbn": "9780345534835",
        "publication_year": 1937,
        "description": "The adventure of Bilbo Baggins, a hobbit who embarks on an unexpected journey to reclaim the lost Dwarf Kingdom of Erebor from the fearsome dragon Smaug.",
        "tags": ["Fiction", "Fantasy", "Classic"]
    },
    {
        "title": "Harry Potter and the Philosopher's Stone",
        "author": "J.K. Rowling",
        "category": "Fantasy",
        "isbn": "9780590353427",
        "publication_year": 1997,
        "description": "The first novel in the Harry Potter series, it follows Harry Potter, a young wizard who discovers his magical heritage on his eleventh birthday, when he receives a letter of acceptance to Hogwarts School of Witchcraft and Wizardry.",
        "tags": ["Fiction", "Fantasy", "Young Adult"]
    },
    {
        "title": "The Catcher in the Rye",
        "author": "J.D. Salinger",
        "category": "Fiction",
        "isbn": "9780316769488",
        "publication_year": 1951,
        "description": "The story of Holden Caulfield, a teenage boy who has been expelled from prep school and is wandering around New York City. It deals with complex issues of innocence, identity, belonging, loss, and connection.",
        "tags": ["Fiction", "Classic", "Young Adult"]
    },
    {
        "title": "The Da Vinci Code",
        "author": "Dan Brown",
        "category": "Thriller",
        "isbn": "9780307474278",
        "publication_year": 2003,
        "description": "A mystery thriller novel that follows symbologist Robert Langdon and cryptologist Sophie Neveu as they investigate a murder in Paris's Louvre Museum and discover a battle between the Priory of Sion and Opus Dei over the possibility of Jesus Christ having been married to Mary Magdalene.",
        "tags": ["Fiction", "Thriller", "Mystery"]
    },
    {
        "title": "The Alchemist",
        "author": "Paulo Coelho",
        "category": "Fiction",
        "isbn": "9780062315007",
        "publication_year": 1988,
        "description": "A philosophical novel about a young Andalusian shepherd named Santiago who dreams of finding a worldly treasure at the Egyptian pyramids and embarks on a journey to fulfill his personal legend.",
        "tags": ["Fiction", "Philosophy", "Fantasy"]
    },
    {
        "title": "Sapiens: A Brief History of Humankind",
        "author": "Yuval Noah Harari",
        "category": "Non-Fiction",
        "isbn": "9780062316097",
        "publication_year": 2011,
        "description": "A book that surveys the history of humankind from the evolution of archaic human species in the Stone Age up to the twenty-first century, focusing on Homo sapiens.",
        "tags": ["Non-Fiction", "Science", "History"]
    },
    {
        "title": "The Lord of the Rings",
        "author": "J.R.R. Tolkien",
        "category": "Fantasy",
        "isbn": "9780618640157",
        "publication_year": 1954,
        "description": "An epic high-fantasy novel that follows hobbits Frodo Baggins, Sam Gamgee, Merry Brandybuck and Pippin Took as they embark on a quest to destroy the One Ring, which was created by the Dark Lord Sauron.",
        "tags": ["Fiction", "Fantasy", "Classic"]
    },
    {
        "title": "Thinking, Fast and Slow",
        "author": "Daniel Kahneman",
        "category": "Non-Fiction",
        "isbn": "9780374533557",
        "publication_year": 2011,
        "description": "The book summarizes research that Kahneman performed during decades of research, often in collaboration with Amos Tversky, on cognitive biases, prospect theory, and happiness.",
        "tags": ["Non-Fiction", "Psychology", "Business"]
    },
    {
        "title": "The Hunger Games",
        "author": "Suzanne Collins",
        "category": "Science Fiction",
        "isbn": "9780439023528",
        "publication_year": 2008,
        "description": "A dystopian novel set in a post-apocalyptic nation called Panem, where children are selected to compete in a televised annual battle to the death. The story follows Katniss Everdeen, who volunteers to take her younger sister's place in the games.",
        "tags": ["Fiction", "Science Fiction", "Young Adult"]
    },
    {
        "title": "A Brief History of Time",
        "author": "Stephen Hawking",
        "category": "Science",
        "isbn": "9780553380163",
        "publication_year": 1988,
        "description": "A popular-science book that examines the nature of time, the origin and eventual fate of the universe, black holes, and the author's own work on theoretical physics.",
        "tags": ["Non-Fiction", "Science", "Physics"]
    },
    {
        "title": "The Girl with the Dragon Tattoo",
        "author": "Stieg Larsson",
        "category": "Mystery",
        "isbn": "9780307949486",
        "publication_year": 2005,
        "description": "The first book in the Millennium series, it combines murder mystery, family saga, love story, and financial intrigue into a complex and atmospheric novel. The plot follows journalist Mikael Blomkvist and computer hacker Lisbeth Salander.",
        "tags": ["Fiction", "Mystery", "Thriller"]
    },
    {
        "title": "The Little Prince",
        "author": "Antoine de Saint-Exupéry",
        "category": "Fiction",
        "isbn": "9780156012195",
        "publication_year": 1943,
        "description": "A poetic tale that follows a young prince who visits various planets in space, including Earth, and addresses themes of loneliness, friendship, love, and loss.",
        "tags": ["Fiction", "Classic", "Children"]
    },
    {
        "title": "Educated",
        "author": "Tara Westover",
        "category": "Biography",
        "isbn": "9780399590504",
        "publication_year": 2018,
        "description": "A memoir about a young girl who, kept out of school, leaves her survivalist family and goes on to earn a PhD from Cambridge University.",
        "tags": ["Non-Fiction", "Biography", "Memoir"]
    },
    {
        "title": "The Silent Patient",
        "author": "Alex Michaelides",
        "category": "Thriller",
        "isbn": "9781250301697",
        "publication_year": 2019,
        "description": "A psychological thriller about a woman who shoots her husband five times and then never speaks again, and the criminal psychotherapist who is determined to get her to talk and unravel the mystery.",
        "tags": ["Fiction", "Thriller", "Mystery"]
    },
    {
        "title": "Where the Crawdads Sing",
        "author": "Delia Owens",
        "category": "Fiction",
        "isbn": "9780735219090",
        "publication_year": 2018,
        "description": "A novel about a young woman named Kya, who is abandoned by her family and raises herself in the marshes of North Carolina. The story intertwines a coming-of-age narrative with a murder mystery.",
        "tags": ["Fiction", "Mystery", "Romance"]
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "category": "Self-Help",
        "isbn": "9780735211292",
        "publication_year": 2018,
        "description": "A guide to building good habits and breaking bad ones, using a framework that focuses on making small 1% improvements through four simple steps: make it obvious, make it attractive, make it easy, and make it satisfying.",
        "tags": ["Non-Fiction", "Self-Help", "Psychology"]
    }
]

def create_tags():
    """Create tags if they don't exist."""
    existing_tags = {tag.name: tag for tag in BookTag.query.all()}
    
    for tag_name in TAGS:
        if tag_name not in existing_tags:
            new_tag = BookTag(name=tag_name)
            db.session.add(new_tag)
    
    db.session.commit()
    return {tag.name: tag for tag in BookTag.query.all()}


def add_books(tag_dict):
    """Add books to the database."""
    existing_isbns = {book.isbn for book in Book.query.all() if book.isbn}
    books_added = 0
    
    for book_data in BOOKS:
        # Skip if ISBN already exists
        if book_data["isbn"] in existing_isbns:
            print(f"Book with ISBN {book_data['isbn']} already exists. Skipping.")
            continue
        
        # Create new book
        new_book = Book(
            title=book_data["title"],
            author=book_data["author"],
            category=book_data["category"],
            isbn=book_data["isbn"],
            publication_year=book_data["publication_year"],
            description=book_data["description"],
            status="available",
            created_at=datetime.utcnow()
        )
        
        # Add book to session
        db.session.add(new_book)
        db.session.flush()  # Get the book ID
        
        # Add tags
        for tag_name in book_data["tags"]:
            if tag_name in tag_dict:
                new_book.tags.append(tag_dict[tag_name])
        
        books_added += 1
    
    db.session.commit()
    return books_added


if __name__ == "__main__":
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Create admin user if none exists
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@library.com",
                password_hash=generate_password_hash("admin"),
                is_admin=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print("Created admin user")
        
        # Create tags
        tag_dict = create_tags()
        print(f"Created/verified {len(tag_dict)} tags")
        
        # Add books
        books_added = add_books(tag_dict)
        print(f"Added {books_added} new books to the library")