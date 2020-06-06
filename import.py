import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

with open('books.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    next(csv_reader)
    try:
        for row in csv_reader:
            db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                        {"isbn": row[0], "title": row[1], "author": row[2], "year": row[3]})
            print(f"[IMPORTED] ISBN: {row[0]}, Title: {row[1]}, Author: {row[2]}, Year: {row[3]}")
    except:
        print(f"[Error] ISBN: {row[0]}, Title: {row[1]}, Author: {row[2]}, Year: {row[3]}")
    else:
        print("All books imported successfully!")
    finally:
        db.commit()
