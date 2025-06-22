# Import Libraries
from flask import Flask, render_template, request, jsonify
import pymysql
import pymysql.cursors

app = Flask(__name__)

# Connecting to mysql
mysql_conn = pymysql.connect(
    host = '',
    user = '',
    password = '',
    database=''
)

with mysql_conn.cursor() as cursor:
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print("MySQL version:", version[0])

# Home Page
@app.route('/')
def home():
    return render_template("index.html")


# Returns all books in inventory
@app.route('/api/inventory', methods=['GET'])
def inventory():
    try:
        with mysql_conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT b.book_id, b.title, CONCAT(a.first_name," ", a.last_name) AS Author, b.published_year, b.price,i.quantity as Inventory ' \
            'FROM books b ' \
            'LEFT JOIN inventory i ON b.book_id = i.book_id LEFT JOIN book_author ba ON b.book_id = ba.book_id LEFT JOIN authors a ON ba.author_id = a.author_id')
            book_list = cursor.fetchall()
            return jsonify(book_list), 200
    except Exception as e:
        return f"Error fetching inventory: {e}"

# Adds a book in the books table
@app.route('/api/add', methods=['POST'])
def add_book():
        title = request.json['title']
        isbn = request.json['isbn']
        published_year = request.json['published_year']
        price = request.json['price']

        try:
            with mysql_conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO books (title, isbn, published_year, price) VALUES (%s, %s, %s,%s)",
                    (title, isbn, published_year,price)
                )
                mysql_conn.commit()
                book_id = cursor.lastrowid #gets last book_id
            return jsonify({
            "message": "Book added successfully",
            "book": {
                "book_id": book_id,
                "title": title,
                "isbn": isbn,
                "published_year": int(published_year),
                "price": float(price),
            }
        }), 201
        except Exception as e:
            return f"Error adding book: {e}"
        
# Uses book_id to find books in the books table. Also joins inventory to show quantity
@app.route('/api/search', methods=['GET'])
def api_search():
    id = request.args.get('book_id')

    try:
        with mysql_conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute('SELECT b.book_id, b.title, CONCAT(a.first_name," ", a.last_name) AS Author, b.published_year, b.price,i.quantity as Inventory ' \
            'FROM books b ' \
            'LEFT JOIN inventory i ON b.book_id = i.book_id LEFT JOIN book_author ba ON b.book_id = ba.book_id LEFT JOIN authors a ON ba.author_id = a.author_id WHERE b.book_id = %s', (id))
            book_list = cursor.fetchall()

            if not book_list:
                return jsonify({"error": "Book not found with matching ID"}), 404  # No book match

        return jsonify(book_list), 200  # Book found

    except Exception as e:
        return f"Error Searching for book: {e}"
    

# Updates partial fields using book_id
@app.route('/api/books/<int:book_id>', methods=['PATCH'])
def update_book(book_id):
    data = request.json
    fields = []
    values = []

    # Only include fields that are present and the values we want to change 
    if 'title' in data:
        fields.append("title = %s")
        values.append(data['title'])
    if 'isbn' in data:
        fields.append("isbn = %s")
        values.append(data['isbn'])
    if 'published_year' in data:
        fields.append("published_year = %s")
        values.append(data['published_year'])
    if 'price' in data:
        fields.append("price = %s")
        values.append(data['price'])

    if not fields:
        return jsonify({"error": "No fields provided for update"}), 400

    # Adds the book_id for where clause
    values.append(book_id)

    # Sets the sql query to only include the fields that want to be updated
    query = f"UPDATE books SET {', '.join(fields)} WHERE book_id = %s"

    try:
        with mysql_conn.cursor() as cursor:
            # Excutes the fields and values that we want
            cursor.execute(query, tuple(values))
            mysql_conn.commit()

        return jsonify({
            "message": "Book updated successfully",
            "book": {
                "book_id": book_id,
                **{i: data[i] for i in data if i in ['title', 'isbn', 'published_year', 'price']}
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Deletes records by book_id
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    id = book_id

    try:
        with mysql_conn.cursor() as cursor:
            cursor.execute("DELETE FROM books WHERE book_id = %s",(id))
            mysql_conn.commit

            if cursor.rowcount == 0:
                return jsonify({"error": f"Book {id} not found"}), 404
            
            return jsonify({
                 "message": f"Book {id} deleted successfully"
                 }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)
