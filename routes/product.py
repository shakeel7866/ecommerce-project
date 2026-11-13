import os
import uuid
from werkzeug.utils import secure_filename  # kept for optional use

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE = True
except Exception:
    TfidfVectorizer = None
    cosine_similarity = None
    AI_AVAILABLE = False

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from database.db import mysql

product = Blueprint("product", __name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# =========================
# Product List (Admin)
# =========================
@product.route("/admin/products")
def product_list():

    search = request.args.get("search", "")
    sort_by = request.args.get("sort_by", "id_asc")

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    products_count = cur.fetchone()[0]

    query = """
        SELECT
            products.id,
            products.product_name,
            categories.category_name,
            products.stock,
            products.status,
            products.created_at,
            products.price,
            products.original_price,
            products.discount_percent,
            products.image,
            brands.brand_name,
            products.rating
        FROM products
        INNER JOIN categories
            ON products.category_id = categories.id
        INNER JOIN brands
            ON products.brand_id = brands.id
    """

    if search:
        query += """
        WHERE
            products.product_name LIKE %s
            OR categories.category_name LIKE %s
            OR brands.brand_name LIKE %s
        """

    sort_map = {
        "id_asc": "products.id ASC",
        "id_desc": "products.id DESC",
        "name_asc": "products.product_name ASC",
        "name_desc": "products.product_name DESC",
        "price_asc": "products.price ASC",
        "price_desc": "products.price DESC",
        "stock_asc": "products.stock ASC",
        "stock_desc": "products.stock DESC",
        "newest": "products.created_at DESC",
        "oldest": "products.created_at ASC",
    }
    query += " ORDER BY " + sort_map.get(sort_by, "products.id ASC")

    if search:
        value = "%" + search + "%"
        cur.execute(query, (value, value, value))
    else:
        cur.execute(query)

    products = cur.fetchall()
    cur.close()

    return render_template(
        "admin/products/list.html",
        products=products,
        search=search,
        sort_by=sort_by,
        products_count=products_count,
    )


# =========================
# Add Product (Admin)
# =========================
@product.route("/admin/products/add", methods=["GET", "POST"])
def add_product():

    cur = mysql.connection.cursor()

    cur.execute("SELECT id, category_name FROM categories ORDER BY category_name ASC")
    categories = cur.fetchall()

    cur.execute("SELECT id, brand_name FROM brands ORDER BY brand_name ASC")
    brands = cur.fetchall()

    if request.method == "POST":

        category_id = request.form["category_id"]
        brand_id = request.form["brand_id"]
        product_name = request.form["product_name"]
        sku = request.form["sku"]
        barcode = request.form.get("barcode", "")
        description = request.form["description"]
        price = request.form["price"]
        original_price = request.form["original_price"]
        discount_percent = request.form["discount_percent"]
        stock = request.form["stock"]

        # Check Duplicate SKU
        cur.execute("SELECT id FROM products WHERE sku=%s", (sku,))
        if cur.fetchone():
            cur.close()
            flash("SKU already exists! Please use a different SKU.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                brands=brands,
                form_data=request.form,
            )

        # Ensure upload dir exists once
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Main image
        image = request.files.get("image")
        filename = None

        if image and image.filename != "":
            extension = os.path.splitext(image.filename)[1].lower()

            if extension not in ALLOWED_EXTENSIONS:
                cur.close()
                flash("Invalid file format! Allowed: JPG, JPEG, PNG, WEBP", "danger")
                return render_template(
                    "admin/products/add.html",
                    categories=categories,
                    brands=brands,
                    form_data=request.form,
                )

            filename = f"{uuid.uuid4().hex}{extension}"
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        try:
            # Insert Product
            cur.execute(
                """
                INSERT INTO products
                (
                    category_id,
                    brand_id,
                    product_name,
                    sku,
                    barcode,
                    description,
                    price,
                    original_price,
                    discount_percent,
                    stock,
                    image
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    category_id,
                    brand_id,
                    product_name,
                    sku,
                    barcode,
                    description,
                    price,
                    original_price,
                    discount_percent,
                    stock,
                    filename,
                ),
            )

            product_id = cur.lastrowid

            # Gallery images
            gallery_images = request.files.getlist("gallery")
            for img in gallery_images:
                if img and img.filename != "":
                    ext = os.path.splitext(img.filename)[1].lower()
                    if ext in ALLOWED_EXTENSIONS:
                        gallery_filename = f"{uuid.uuid4().hex}{ext}"
                        img.save(os.path.join(UPLOAD_FOLDER, gallery_filename))

                        cur.execute(
                            """
                            INSERT INTO product_images
                            (product_id, image)
                            VALUES (%s, %s)
                            """,
                            (product_id, gallery_filename),
                        )

            mysql.connection.commit()

        except Exception as e:
            mysql.connection.rollback()
            current_app.logger.exception("Error adding product: %s", e)
            cur.close()
            flash("Something went wrong while saving the product.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                brands=brands,
                form_data=request.form,
            )

        cur.close()
        flash("Product Added Successfully!", "success")
        return redirect(url_for("product.product_list"))

    cur.close()
    return render_template(
        "admin/products/add.html", categories=categories, brands=brands, form_data={}
    )


# =========================
# Edit Product (Admin)
# =========================
@product.route("/admin/products/edit/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    cur = mysql.connection.cursor()

    cur.execute("SELECT id, category_name FROM categories ORDER BY category_name ASC")
    categories = cur.fetchall()

    cur.execute("SELECT id, brand_name FROM brands ORDER BY brand_name ASC")
    brands = cur.fetchall()

    cur.execute(
        """
        SELECT
            id,
            category_id,
            brand_id,
            product_name,
            sku,
            barcode,
            description,
            price,
            original_price,
            discount_percent,
            stock,
            image
        FROM products
        WHERE id=%s
        """,
        (id,),
    )
    product_data = cur.fetchone()

    if not product_data:
        cur.close()
        flash("Product not found!", "danger")
        return redirect(url_for("product.product_list"))

    if request.method == "POST":
        category_id = request.form["category_id"]
        brand_id = request.form["brand_id"]
        product_name = request.form["product_name"]
        sku = request.form["sku"]
        barcode = request.form.get("barcode", "")
        description = request.form["description"]
        price = request.form["price"]
        original_price = request.form["original_price"]
        discount_percent = request.form["discount_percent"]
        stock = request.form["stock"]

        # Existing image (index 11 in the SELECT above)
        filename = product_data[11]

        image = request.files.get("image")

        if image and image.filename != "":
            extension = os.path.splitext(image.filename)[1].lower()

            if extension not in ALLOWED_EXTENSIONS:
                cur.close()
                flash("Invalid file format! Allowed: JPG, JPEG, PNG, WEBP", "danger")
                return render_template(
                    "admin/products/edit.html",
                    product=product_data,
                    categories=categories,
                    brands=brands,
                )

            # Delete old image
            if filename:
                old_file = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except OSError:
                        current_app.logger.warning("Could not delete %s", old_file)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = f"{uuid.uuid4().hex}{extension}"
            image.save(os.path.join(UPLOAD_FOLDER, filename))

        try:
            cur.execute(
                """
                UPDATE products
                SET
                    category_id=%s,
                    brand_id=%s,
                    product_name=%s,
                    sku=%s,
                    barcode=%s,
                    description=%s,
                    price=%s,
                    original_price=%s,
                    discount_percent=%s,
                    stock=%s,
                    image=%s
                WHERE id=%s
                """,
                (
                    category_id,
                    brand_id,
                    product_name,
                    sku,
                    barcode,
                    description,
                    price,
                    original_price,
                    discount_percent,
                    stock,
                    filename,
                    id,
                ),
            )
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            current_app.logger.exception("Error updating product %s: %s", id, e)
            cur.close()
            flash("Something went wrong while updating the product.", "danger")
            return render_template(
                "admin/products/edit.html",
                product=product_data,
                categories=categories,
                brands=brands,
            )

        cur.close()
        flash("Product Updated Successfully!", "success")
        return redirect(url_for("product.product_list"))

    cur.close()
    return render_template(
        "admin/products/edit.html",
        product=product_data,
        categories=categories,
        brands=brands,
    )


# =========================
# Delete Product (Admin)
# =========================
@product.route("/admin/products/delete/<int:id>", methods=["POST"])
def delete_product(id):
    cur = mysql.connection.cursor()

    # Get product image
    cur.execute("SELECT image FROM products WHERE id=%s", (id,))
    product = cur.fetchone()

    # Get gallery images
    cur.execute("SELECT image FROM product_images WHERE product_id=%s", (id,))
    gallery = cur.fetchall()

    try:
        # Delete related gallery rows first
        cur.execute("DELETE FROM product_images WHERE product_id=%s", (id,))
        # Delete product
        cur.execute("DELETE FROM products WHERE id=%s", (id,))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        current_app.logger.exception("Error deleting product %s: %s", id, e)
        cur.close()
        flash("Something went wrong while deleting the product.", "danger")
        return redirect(url_for("product.product_list"))

    cur.close()

    # Now remove files from disk
    if product and product[0]:
        image_file = os.path.join(UPLOAD_FOLDER, product[0])
        if os.path.exists(image_file):
            try:
                os.remove(image_file)
            except OSError:
                current_app.logger.warning("Could not delete %s", image_file)

    for row in gallery:
        if row and row[0]:
            gfile = os.path.join(UPLOAD_FOLDER, row[0])
            if os.path.exists(gfile):
                try:
                    os.remove(gfile)
                except OSError:
                    current_app.logger.warning("Could not delete %s", gfile)

    flash("Product deleted successfully!", "success")
    return redirect(url_for("product.product_list"))


# =========================
# Product Details (Frontend)
# =========================
@product.route("/product/<int:id>")
def product_details(id):
    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
            products.id,
            products.product_name,
            products.sku,
            products.barcode,
            products.description,
            products.price,
            products.original_price,
            products.discount_percent,
            products.stock,
            products.image,
            products.rating,
            products.created_at,
            categories.category_name,
            categories.id AS category_id,
            brands.brand_name,
            brands.id AS brand_id
        FROM products
        INNER JOIN categories
            ON products.category_id = categories.id
        INNER JOIN brands
            ON products.brand_id = brands.id
        WHERE products.id=%s
        """,
        (id,),
    )
    product_data = cur.fetchone()

    if not product_data:
        cur.close()
        flash("Product not found!", "danger")
        return redirect(url_for("home"))

    # Unpack product data into named variables
    p_id = product_data[0]
    p_name = product_data[1] or ""
    p_description = product_data[4] or ""
    p_price = float(product_data[5] or 0)
    p_rating = float(product_data[10] or 0)
    p_category_id = product_data[13]
    p_brand_id = product_data[15]

    # =========================
    # Save Product View (No Duplicates)
    # =========================
    customer_id = session.get("customer_id")

    if customer_id:
        cur.execute(
            """
            SELECT id
            FROM product_views
            WHERE customer_id=%s AND product_id=%s
            LIMIT 1
            """,
            (customer_id, id),
        )
        existing_view = cur.fetchone()

        if existing_view:
            cur.execute(
                "UPDATE product_views SET viewed_at = CURRENT_TIMESTAMP WHERE id=%s",
                (existing_view[0],),
            )
        else:
            cur.execute(
                """
                INSERT INTO product_views
                (customer_id, product_id, viewed_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                """,
                (customer_id, id),
            )
        mysql.connection.commit()

    # Gallery
    cur.execute(
        "SELECT image FROM product_images WHERE product_id=%s ORDER BY id ASC",
        (id,),
    )
    gallery = cur.fetchall()

    # Reviews
    cur.execute(
        """
        SELECT id, customer_name, rating, review, created_at
        FROM product_reviews
        WHERE product_id=%s
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (id,),
    )
    reviews = cur.fetchall()

    # Rating summary
    cur.execute(
        """
        SELECT COUNT(*) AS total_reviews, ROUND(AVG(rating), 1) AS avg_rating
        FROM product_reviews
        WHERE product_id=%s
        """,
        (id,),
    )
    rating_summary = cur.fetchone()

    # =========================
    # User Behavior Analysis (cached once)
    # =========================
    viewed_products = []
    view_counts = {}          # product_id -> count
    viewed_preferences = []   # list of (category_id, brand_id) per view row

    if customer_id:
        cur.execute(
            """
            SELECT
                p.category_id,
                p.brand_id,
                COUNT(*) as view_count,
                MAX(pv.viewed_at) as last_viewed,
                DATEDIFF(NOW(), MAX(pv.viewed_at)) as days_since_last_view
            FROM product_views pv
            INNER JOIN products p ON pv.product_id = p.id
            WHERE pv.customer_id = %s
            AND pv.viewed_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY p.category_id, p.brand_id
            ORDER BY view_count DESC, days_since_last_view ASC
            LIMIT 5
            """,
            (customer_id,),
        )
        viewed_products = cur.fetchall()

        # Product-level view counts
        cur.execute(
            """
            SELECT product_id, COUNT(*)
            FROM product_views
            WHERE customer_id=%s
            GROUP BY product_id
            """,
            (customer_id,),
        )
        view_counts = {row[0]: int(row[1]) for row in cur.fetchall()}

        # Category/brand preference rows (fetched ONCE)
        cur.execute(
            """
            SELECT p.category_id, p.brand_id
            FROM product_views pv
            JOIN products p ON p.id = pv.product_id
            WHERE pv.customer_id=%s
            """,
            (customer_id,),
        )
        viewed_preferences = cur.fetchall()

    # Aggregate preferences with recency weighting
    user_category_preferences = {}
    user_brand_preferences = {}

    for row in viewed_products:
        category_id = row[0]
        brand_id = row[1]
        view_count = row[2]
        days_since_last_view = row[4] if row[4] is not None else 999

        recency_weight = max(0, 1 - (days_since_last_view / 30))
        weighted_score = view_count * (1 + recency_weight)

        if category_id:
            user_category_preferences[category_id] = (
                user_category_preferences.get(category_id, 0) + weighted_score
            )
        if brand_id:
            user_brand_preferences[brand_id] = (
                user_brand_preferences.get(brand_id, 0) + weighted_score
            )

    # =========================
    # Hybrid AI Recommendations
    # =========================
    cur.execute(
        """
        SELECT
            id,
            product_name,
            description,
            price,
            image,
            category_id,
            brand_id,
            rating,
            stock
        FROM products
        WHERE id != %s
        """,
        (id,),
    )
    all_products = cur.fetchall()

    recommended_products = []

    if all_products:

        current_text = f"{p_name} {p_description}".lower()

        product_texts = []
        for p in all_products:
            name = p[1] or ""
            desc = p[2] or ""
            product_texts.append(f"{name} {desc}".lower())

        # TF-IDF similarity (only if sklearn is available)
        if AI_AVAILABLE:
            try:
                texts = [current_text] + product_texts
                vectorizer = TfidfVectorizer(
                    stop_words="english",
                    max_features=500,
                    ngram_range=(1, 2),
                )
                tfidf_matrix = vectorizer.fit_transform(texts)
                similarity_scores = cosine_similarity(
                    tfidf_matrix[0:1], tfidf_matrix[1:]
                )[0]
            except Exception as e:
                current_app.logger.exception("TF-IDF failed: %s", e)
                similarity_scores = [0] * len(all_products)
        else:
            similarity_scores = [0] * len(all_products)

        # Precompute preference hits (distinct products)
        cat_hits = {}
        brand_hits = {}
        for cat, brd in viewed_preferences:
            if cat:
                cat_hits[cat] = cat_hits.get(cat, 0) + 1
            if brd:
                brand_hits[brd] = brand_hits.get(brd, 0) + 1

        scored_products = []

        for index, p in enumerate(all_products):
            product_id = p[0]
            product_price = float(p[3] or 0)
            product_category = p[5]
            product_brand = p[6]
            product_rating = float(p[7] or 0)
            product_stock = int(p[8] or 0)

            if product_stock <= 0:
                continue

            # Behavior score (max 10)
            behavior_score = min(view_counts.get(product_id, 0) * 5, 10)

            # Preference score (max 15) — based on distinct product hits
            preference_score = 0
            if product_category in cat_hits:
                preference_score += min(cat_hits[product_category] * 3, 8)
            if product_brand in brand_hits:
                preference_score += min(brand_hits[product_brand] * 2, 7)
            preference_score = min(preference_score, 15)

            # AI scores
            text_score = float(similarity_scores[index]) * 40
            category_score = 20 if product_category == p_category_id else 0
            brand_score = 15 if product_brand == p_brand_id else 0

            # Price similarity
            price_score = 0
            if p_price > 0 and product_price > 0:
                price_difference = abs(p_price - product_price)
                max_price = max(p_price, product_price)
                price_similarity = max(0, 1 - (price_difference / max_price))
                price_score = price_similarity * 15

            # Rating score
            rating_score = min(product_rating * 2, 10)

            final_score = (
                text_score
                + category_score
                + brand_score
                + behavior_score
                + preference_score
                + price_score
                + rating_score
            )
            final_score = min(final_score, 100)

            scored_products.append((final_score, p))

        scored_products.sort(key=lambda x: x[0], reverse=True)
        recommended_products = [
            (prod, round(score, 2)) for score, prod in scored_products[:4]
        ]

    # Specifications
    cur.execute(
        """
        SELECT spec_name, spec_value
        FROM product_specifications
        WHERE product_id=%s
        ORDER BY id ASC
        """,
        (id,),
    )
    specifications = cur.fetchall()

    cur.close()

    return render_template(
        "products/view.html",
        product=product_data,
        reviews=reviews,
        rating_summary=rating_summary,
        recommended_products=recommended_products,
        gallery=gallery,
        specifications=specifications,
        viewed_products=viewed_products,
    )


# =========================
# Add Review (Frontend)
# =========================
@product.route("/product/review", methods=["POST"])
def add_review():

    if "customer_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("auth.login"))

    product_id = request.form["product_id"]
    rating_raw = request.form["rating"]
    review = request.form.get("review", "").strip()

    # Validate rating
    try:
        rating = int(rating_raw)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        flash("Invalid rating. Please choose between 1 and 5.", "danger")
        return redirect(url_for("product.product_details", id=product_id))

    cur = mysql.connection.cursor()

    # Prevent duplicate reviews from the same customer
    cur.execute(
        "SELECT id FROM product_reviews WHERE product_id=%s AND customer_id=%s",
        (product_id, session["customer_id"]),
    )
    if cur.fetchone():
        cur.close()
        flash("You have already reviewed this product.", "warning")
        return redirect(url_for("product.product_details", id=product_id))

    try:
        cur.execute(
            """
            INSERT INTO product_reviews
            (product_id, customer_id, customer_name, rating, review)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                product_id,
                session["customer_id"],
                session["customer_name"],
                rating,
                review,
            ),
        )

        # Update product's average rating
        cur.execute(
            "SELECT AVG(rating) FROM product_reviews WHERE product_id=%s",
            (product_id,),
        )
        avg_rating = cur.fetchone()[0]

        cur.execute(
            "UPDATE products SET rating=%s WHERE id=%s",
            (round(avg_rating, 1) if avg_rating else 0, product_id),
        )

        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        current_app.logger.exception("Error adding review: %s", e)
        cur.close()
        flash("Something went wrong while submitting your review.", "danger")
        return redirect(url_for("product.product_details", id=product_id))

    cur.close()
    flash("Review Submitted Successfully!", "success")
    return redirect(url_for("product.product_details", id=product_id))