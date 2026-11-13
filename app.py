from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
)
from flask_bcrypt import Bcrypt
from config import Config
from database.db import mysql
from mysql.connector.cursor import MySQLCursorDict as DictCursor
from routes.auth import auth
from routes.dashboard import dashboard
from routes.category import category
from routes.brand import brand
from routes.product import product
from routes.order import order
from routes.customer import customer
from routes.supplier import supplier
from routes.purchase import purchase
from routes.purchase_return import purchase_return
from routes.sales import sales
from routes.sales_return import sales_return
from routes.report import report
from routes.cart import cart
from routes.stock import stock
from routes.wishlist import wishlist
from routes.user import user
from routes.coupon import coupon
from routes.review import review
from routes.contact import contact
from routes.expense import expense

app = Flask(__name__)
app.config.from_object(Config)

mysql.init_app(app)
bcrypt = Bcrypt(app)

# Register all blueprints
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(category)
app.register_blueprint(brand)
app.register_blueprint(product)
app.register_blueprint(order)
app.register_blueprint(customer)
app.register_blueprint(supplier)
app.register_blueprint(purchase)
app.register_blueprint(purchase_return)
app.register_blueprint(sales)
app.register_blueprint(sales_return)
app.register_blueprint(report)
app.register_blueprint(cart)
app.register_blueprint(stock)
app.register_blueprint(wishlist)
app.register_blueprint(user)
app.register_blueprint(coupon)
app.register_blueprint(review)
app.register_blueprint(contact)
app.register_blueprint(expense)


@app.context_processor
def cart_count():
    cart = session.get("cart", {})
    count = sum(item["qty"] for item in cart.values())
    return dict(cart_count=count)


@app.context_processor
def inject_nav_categories():
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            SELECT id, category_name
            FROM categories
            ORDER BY category_name
        """)
        nav_categories = cur.fetchall()
    finally:
        cur.close()
    return dict(nav_categories=nav_categories)


@app.route("/")
def home():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            products.id,
            products.product_name,
            products.price,
            products.original_price,
            products.discount_percent,
            products.image,
            brands.brand_name,
            products.rating
        FROM products
        INNER JOIN brands
            ON products.brand_id = brands.id
        ORDER BY products.id DESC
        LIMIT 8
    """)

    products = cur.fetchall()
    cur.close()

    return render_template("index.html", products=products)


@app.route("/shop")
def shop():
    search = request.args.get("search", "")
    cur = mysql.connection.cursor()

    if search:
        cur.execute(
            """
            SELECT
                products.id,
                products.product_name,
                products.price,
                products.original_price,
                products.discount_percent,
                products.image,
                brands.brand_name,
                products.rating
            FROM products
            INNER JOIN brands
                ON products.brand_id = brands.id
            WHERE
                products.product_name LIKE %s
                OR brands.brand_name LIKE %s
            ORDER BY products.id DESC
            """,
            (
                "%" + search + "%",
                "%" + search + "%",
            ),
        )
    else:
        cur.execute("""
            SELECT
                products.id,
                products.product_name,
                products.price,
                products.original_price,
                products.discount_percent,
                products.image,
                brands.brand_name,
                products.rating
            FROM products
            INNER JOIN brands
                ON products.brand_id = brands.id
            ORDER BY products.id DESC
        """)

    products = cur.fetchall()
    cur.close()

    return render_template("shop.html", products=products)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/categories")
def categories():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            category_name
        FROM categories
        ORDER BY category_name
    """)

    categories = cur.fetchall()
    cur.close()

    return render_template("categories.html", categories=categories)


# NOTE: /categories/<category_name> route ab routes/category.py mein shift ho gaya hai.


@app.route("/contact", methods=["GET", "POST"])
def contact_page():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill all required fields.", "warning")
            return redirect("/contact")

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO contact_messages
            (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, subject, message),
        )

        mysql.connection.commit()
        cur.close()

        flash("Your message has been sent successfully!", "success")

        return redirect("/contact")

    return render_template("contact.html")


@app.route("/shop/new-arrivals")
def new_arrivals():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            products.id,
            products.product_name,
            products.price,
            products.original_price,
            products.discount_percent,
            products.image,
            brands.brand_name,
            products.rating
        FROM products
        INNER JOIN brands
            ON products.brand_id = brands.id
        ORDER BY products.id DESC
        LIMIT 12
    """)

    rows = cur.fetchall()
    cur.close()

    products = [
        {
            "id": row[0],
            "product_name": row[1],
            "price": row[2],
            "original_price": row[3],
            "discount_percent": row[4],
            "image": row[5],
            "brand_name": row[6],
            "rating": row[7],
        }
        for row in rows
    ]

    return render_template(
        "shop/new_arrivals.html",
        products=products
    )


@app.route("/shop/best-sellers")
def best_sellers():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            products.id,
            products.product_name,
            products.price,
            products.original_price,
            products.discount_percent,
            products.image,
            brands.brand_name,
            products.rating
        FROM products
        INNER JOIN brands
            ON products.brand_id = brands.id
        ORDER BY products.rating DESC, products.id DESC
        LIMIT 12
    """)

    rows = cur.fetchall()
    cur.close()

    products = [
        {
            "id": row[0],
            "product_name": row[1],
            "price": row[2],
            "original_price": row[3],
            "discount_percent": row[4],
            "image": row[5],
            "brand_name": row[6],
            "rating": row[7],
        }
        for row in rows
    ]

    return render_template(
        "shop/best_sellers.html",
        products=products
    )


@app.route("/shop/sale")
def sale():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            products.id,
            products.product_name,
            products.price,
            products.original_price,
            products.discount_percent,
            products.image,
            brands.brand_name,
            products.rating
        FROM products
        INNER JOIN brands
            ON products.brand_id = brands.id
        WHERE products.discount_percent > 0
        ORDER BY products.discount_percent DESC, products.id DESC
        LIMIT 12
    """)

    rows = cur.fetchall()
    cur.close()

    products = [
        {
            "id": row[0],
            "product_name": row[1],
            "price": row[2],
            "original_price": row[3],
            "discount_percent": row[4],
            "image": row[5],
            "brand_name": row[6],
            "rating": row[7],
        }
        for row in rows
    ]

    return render_template(
        "shop/sale.html",
        products=products
    )


# Start Flask application
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
