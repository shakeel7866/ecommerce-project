
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.db import mysql

category = Blueprint("category", __name__)


# =====================================
# ADMIN: CATEGORY LIST
# =====================================
@category.route("/admin/categories")
def admin_categories():

    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            SELECT id, category_name, description, status, created_at
            FROM categories
            ORDER BY id DESC
        """)
        categories = cur.fetchall()

    finally:
        cur.close()

    return render_template(
        "admin/categories/list.html",
        categories=categories
    )


# =====================================
# ADMIN: ADD CATEGORY
# =====================================
@category.route("/admin/categories/add", methods=["GET", "POST"])
def add_category():

    if request.method == "POST":

        category_name = request.form.get("category_name", "").strip()
        description = request.form.get("description", "").strip()

        if not category_name:
            flash("Category name is required.", "warning")
            return redirect(url_for("category.add_category"))

        cur = mysql.connection.cursor()

        try:
            cur.execute("""
                INSERT INTO categories (category_name, description)
                VALUES (%s, %s)
            """, (category_name, description))

            mysql.connection.commit()
            flash("Category added successfully!", "success")

        except Exception as e:
            mysql.connection.rollback()
            flash("Unable to add category: " + str(e), "danger")

        finally:
            cur.close()

        return redirect(url_for("category.admin_categories"))

    return render_template("admin/categories/add.html")


# =====================================
# ADMIN: EDIT CATEGORY
# =====================================
@category.route("/admin/categories/edit/<int:id>", methods=["GET", "POST"])
def edit_category(id):

    cur = mysql.connection.cursor()

    try:
        if request.method == "POST":

            category_name = request.form.get("category_name", "").strip()
            description = request.form.get("description", "").strip()

            if not category_name:
                flash("Category name is required.", "warning")
                return redirect(url_for("category.edit_category", id=id))

            cur.execute("""
                UPDATE categories
                SET category_name = %s, description = %s
                WHERE id = %s
            """, (category_name, description, id))

            mysql.connection.commit()
            flash("Category updated successfully!", "success")

            return redirect(url_for("category.admin_categories"))

        cur.execute("""
            SELECT id, category_name, description
            FROM categories
            WHERE id = %s
        """, (id,))

        category_data = cur.fetchone()

    finally:
        cur.close()

    if not category_data:
        flash("Category not found.", "warning")
        return redirect(url_for("category.admin_categories"))

    return render_template(
        "admin/categories/edit.html",
        category=category_data
    )


# =====================================
# ADMIN: DELETE CATEGORY
# =====================================
@category.route("/admin/categories/delete/<int:id>")
def delete_category(id):

    cur = mysql.connection.cursor()

    try:
        cur.execute(
            "DELETE FROM categories WHERE id = %s",
            (id,)
        )

        mysql.connection.commit()

        if cur.rowcount:
            flash("Category deleted successfully!", "success")
        else:
            flash("Category not found.", "warning")

    except Exception:
        mysql.connection.rollback()
        flash(
            "Category cannot be deleted because it may be linked to products.",
            "danger"
        )

    finally:
        cur.close()

    return redirect(url_for("category.admin_categories"))


# =====================================
# PUBLIC: CATEGORY PRODUCTS
# =====================================
@category.route("/categories/<category_name>")
def category_products(category_name):

    cur = mysql.connection.cursor()

    try:
        cur.execute("""
            SELECT id, category_name
            FROM categories
            WHERE LOWER(TRIM(category_name)) = LOWER(TRIM(%s))
        """, (category_name,))

        category_data = cur.fetchone()

        if not category_data:
            return "Category not found", 404

        category_id = category_data[0]
        current_category = category_data[1]

        cur.execute("""
            SELECT id, category_name
            FROM categories
            ORDER BY category_name
        """)
        categories = cur.fetchall()

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
            WHERE products.category_id = %s
            ORDER BY products.id DESC
        """, (category_id,))

        rows = cur.fetchall()

    finally:
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
        "shop/category_products.html",
        category=category_data,
        current_category=current_category,
        categories=categories,
        products=products
    )
