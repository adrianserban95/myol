import os
import requests

from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from pyisemail import is_email
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

API_KEY = "hUZY8BMrPYeUU8szuZcybg"
app.config['JSON_SORT_KEYS'] = False
app.jinja_env.globals['SITE_NAME'] = "MyOL"

@app.route("/")
def index():

    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    #check if an user is already logged in
    if "user_id" in session:
        return render_template("error.html", message="You are already logged in.")

    if request.method == "POST":
        #get the form details
        try:
            username = request.form.get("username")
            email = request.form.get("email")
            password = generate_password_hash(request.form.get("password"))
        except Exception:
            return render_template("error.html", message="Something went wrong ...")

        #check if the email is valid using is_email from pyisemail
        if not is_email(email):
            return render_template("error.html", message="Invalid email. Please provide a valid email address to continue.")

        #check if an account with the provided username already exists in the database
        account = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        if account is not None:
            return render_template("error.html", message="An account already exists with this username. Please use a different username or login.")

        #check if an account with the provided email already exists in the database
        account = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
        if account is not None:
            return render_template("error.html", message="An account already exists with this email. Please use a different email address or login.")

        #if the email is valid and no account found with the provided email, then create a new account
        db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :password)", {"username": username, "email": email, "password": password})
        db.commit()

        #render success page if a new account is created
        return render_template("success.html", message="You registered successfully! Please login to access the website.")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    #check if an user is already logged in
    if "user_id" in session:
        return render_template("error.html", message="You are already logged in.")

    if request.method == "POST":
        #get the form details
        try:
            username = request.form.get("username")
            password = request.form.get("password")
        except Exception:
            return render_template("error.html", message="Something went wrong ...")

        #find the user in the database by the username provided in the /login form
        account = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        #error if no account is found using the email provided
        if account is None:
            return render_template("error.html", message="No account registered with the username provided.")

        #if account is found for the username provided check if the password matches the one in the database
        if check_password_hash(account.password, password):
            session["user_id"] = account.id
            session["username"] = account.username
            return render_template("success.html", message="Login successfully!")
        else:
            return render_template("error.html", message="Wrong password!")

    return render_template("login.html")

@app.route("/logout", methods=["GET"])
def logout():
    #check if an user is logged in
    if "user_id" not in session:
        return render_template("error.html", message="You must be logged in!")

    #delete user_id from session dict to logout the user
    del session["user_id"]
    del session["username"]

    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    #check if an user is logged in
    if "user_id" not in session:
        return render_template("error.html", message="You must be logged in!")

    if request.method == "POST":
        try:
            search = request.form.get("search")
            search_by = request.form.get("searchOptions")
        except Exception:
            return render_template("error.html", message="Something went wrong ...")

        #get all the results matching the isbn provided by the user
        if search_by == "isbn":
            result = db.execute("SELECT * FROM books WHERE isbn ILIKE :isbn", {"isbn": f"%{search}%"}).fetchall()
            return render_template("search.html", books=result)

        #get all the results matching the title provided by the user
        elif search_by == "title":
            result = db.execute("SELECT * FROM books WHERE title ILIKE :title", {"title": f"%{search}%"}).fetchall()
            return render_template("search.html", books=result)

        #get all the results matching the author provided by the user
        elif search_by == "author":
            result = db.execute("SELECT * FROM books WHERE author ILIKE :author", {"author": f"%{search}%"}).fetchall()
            return render_template("search.html", books=result)
        else:
            return render_template("error.html", message="You must select a 'Search by' option.")

        return render_template("search.html", option=search_by)

    return render_template("search.html")

@app.route("/book/<string:book_isbn>", methods=["GET", "POST"])
def book(book_isbn):
    goodreads_data = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": API_KEY, "isbns": book_isbn})

    if goodreads_data.status_code == 404: #if the isbn is not in the goodreads database create a fake api response
        goodreads_data = {
            "books":
                [{
                    "ratings_count": "N/A",
                    "average_rating": "N/A"
                }]
        }
    else:
        goodreads_data = goodreads_data.json()

    #get the book details from database
    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    if book_info is None:
        return render_template("error.html", message="ISBN number not found in the database.")

    #get the book reviews
    book_reviews = db.execute("SELECT book_id, user_id, opinion, rating, date, username FROM reviews JOIN users ON reviews.user_id=users.id WHERE book_id = :id", {"id": book_info.id}).fetchall()

    if request.method == "POST":
        if "user_id" not in session:
            return render_template("error.html", message="You must be logged in!")

        #check if the user already left a review for this book
        review = db.execute("SELECT * FROM reviews WHERE book_id = :book_id and user_id = :user_id", {"book_id": book_info.id, "user_id": session["user_id"]}).fetchone()
        if review is not None:
            return render_template("error.html", message="You already left a review for this book.")

        try:
            rating = request.form.get("rating")
            opinion = request.form.get("opinion")
        except Exception:
            return render_template("error.html", message="Something went wrong ...")

        #if the user's review is more than 250 words
        if len(opinion.split()) > 250:
            return render_template("error.html", message="The opinion must not exceed 250 words.")

        db.execute("INSERT INTO reviews (book_id, user_id, opinion, rating, date) VALUES (:book_id, :user_id, :opinion, :rating, :date)", {"book_id": book_info.id, "user_id": session["user_id"], "opinion": opinion, "rating": rating, "date": datetime.now()})
        db.commit()

        return render_template("success.html", message="Review left successfully.")

    return render_template("book.html", book=book_info, reviews=book_reviews, goodreads=goodreads_data)

@app.route("/api/<string:book_isbn>")
def api(book_isbn):
    #attempt to get the book details from the database if the isbn provided exists
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": book_isbn}).fetchone()
    if book is None:
        return jsonify({"error": "ISBN not found in the database."}), 404

    #get the number of reviews and the average rating for the book
    review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book_id = :book_id", {"book_id": book.id})
    average_rating = db.execute("SELECT AVG(rating) FROM reviews WHERE book_id = :book_id", {"book_id": book.id})

    #serialize them
    review_count = {'result': [dict(row) for row in review_count]}
    average_rating = {'result': [dict(row) for row in average_rating]}

    data = {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": review_count["result"][0]["count"],
        "average_score": float(average_rating["result"][0]["avg"])
        }

    return jsonify(data)

@app.route("/usercp", methods=["GET", "POST"])
def usercp():
    #check if the user is logged in
    if "user_id" not in session:
        return render_template("error.html", message="You must be logged in!")

    #double check if the user exists
    user = db.execute("SELECT * FROM users WHERE id = :id", {"id": session["user_id"]}).fetchone()
    if user is None:
        return render_template("error.html", message="No user found using that id.")

    if request.method == "POST":
        #get the form details
        try:
            email = request.form.get("email")
            password = request.form.get("old-password")
            new_password = request.form.get("new-password")
            conf_password = request.form.get("conf-password")
        except Exception:
            return render_template("error.html", message="Something went wrong ...")

        #first of all, check if the (old) password is right
        if check_password_hash(user.password, password):
            if email != user.email: #if the user decided to change the email
                #check if an account with the provided email already exists in the database
                account = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
                if account is not None:
                    return render_template("error.html", message="An account already exists with this email. Please use a different email address.")

                #check if the email is valid using is_email from pyisemail
                if not is_email(email):
                    return render_template("error.html", message="Invalid email. Please provide a valid email address to continue.")

                db.execute("UPDATE users SET email = :email WHERE id = :userid", {"email": email, "userid": user.id})
                db.commit()

            if len(new_password) > 0: #if the user decided to change the password
                if new_password == conf_password:
                    new_password = generate_password_hash(new_password)

                    db.execute("UPDATE users SET password = :password WHERE id = :userid", {"password": new_password, "userid": user.id})
                    db.commit()
                else:
                    return render_template("error.html", message="Please enter the same password for 'New Password' and 'Confirm Password'.")

            return render_template("success.html", message="Profile updated!")
        else:
            return render_template("error.html", message="Wrong password!")

    return render_template("usercp.html", user=user)
