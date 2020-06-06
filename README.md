# CS50's Project 1
##### Web Programming with Python and JavaScript


### This project is a book review website. Users are able to register and log in using their username and password. Once they log in, they are able to search for books, leave reviews for individual books, and see the reviews made by other people. A third-party API by Goodreads is used, another book review website, to pull in ratings from a broader audience. Finally, users are able to query for book details and book reviews programmatically via the website's API.

*Demo:* https://youtu.be/3nX9NLDWfDw

*Programming Languages & Frameworks:*

 - Front-End: HTML, CSS, Bootstrap
 - Back-End: Python, Flask
 - Database: PostgreSQL

#### Files

##### General
 - **application.py** - The application's root
 - **books.csv** - A spreadsheet in CSV format of 5000 different books
 - **db.sql** - The database schema
 - **import.py** - Application to import the books into the PostgreSQL database
 - **requirements.txt** - The necessary Python packages

##### Templates
 - **book.html** - Book's information are displayed on this page
 - **error.html** - Error page - when an error occurs
 - **index.html** - Home page
  - **layout.html** - Default website layout
 - **login.html** - Users can log accessing this page
 - **register.html** - Visitors can create an account
 - **search.html** - Users can search for a specific book accessing this page
 - **success.html** - Success page - when an action is performed succesfully
  - **usercp.html** - Users can change the personal email or/and password on this page

##### Stylesheets
 - **style.css** - The website's default stylesheet in CSS
