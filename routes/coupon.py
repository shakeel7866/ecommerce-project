from flask import Blueprint, render_template, request, redirect, flash, url_for
from database.db import mysql

coupon = Blueprint("coupon", __name__)


@coupon.route("/admin/coupons")
def coupon_list():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            id,
            coupon_code,
            discount_percent,
            minimum_amount,
            expiry_date,
            status
        FROM coupons
        ORDER BY id DESC
    """)

    coupons = cur.fetchall()
    cur.close()

    return render_template("admin/coupons/list.html", coupons=coupons)


@coupon.route("/admin/coupons/add", methods=["GET", "POST"])
def add_coupon():
    if request.method == "POST":
        coupon_code = request.form.get("coupon_code")
        discount_percent = request.form.get("discount_percent")
        minimum_amount = request.form.get("minimum_amount")
        expiry_date = request.form.get("expiry_date")
        status = request.form.get("status")

        # Validation
        if not all(
            [coupon_code, discount_percent, minimum_amount, expiry_date, status]
        ):
            flash("All fields are required!", "danger")
            return render_template("admin/coupons/add.html")

        try:
            discount_percent = float(discount_percent)
            minimum_amount = float(minimum_amount)

            if discount_percent < 0 or discount_percent > 100:
                flash("Discount percent must be between 0 and 100!", "danger")
                return render_template("admin/coupons/add.html")

        except ValueError:
            flash("Invalid numeric values!", "danger")
            return render_template("admin/coupons/add.html")

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO coupons
            (
                coupon_code,
                discount_percent,
                minimum_amount,
                expiry_date,
                status
            )
            VALUES(%s, %s, %s, %s, %s)
            """,
            (coupon_code, discount_percent, minimum_amount, expiry_date, status),
        )

        mysql.connection.commit()
        cur.close()

        flash("Coupon Added Successfully!", "success")
        return redirect(url_for("coupon.coupon_list"))

    return render_template("admin/coupons/add.html")
