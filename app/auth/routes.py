from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from sqlalchemy.exc import SQLAlchemyError

from . import auth_bp
from .services import authenticate_user, create_user

PROVIDER_SUBCATEGORIES = {
    "accommodation": {"hotel", "hostel", "cabin", "apartment", "lodge"},
    "food_drink": {"restaurant", "cafe", "bar", "bakery", "fast_food"},
    "activities_experiences": {
        "tour",
        "adventure",
        "cultural_experience",
        "wellness",
        "nightlife",
    },
    "free_activities": {"park", "viewpoint", "museum_free", "walking_route", "public_space"},
    "tourism_services": {
        "transport",
        "travel_agency",
        "guide",
        "car_rental",
        "information_center",
    },
}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_user"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("Auth/login.html")

        user = authenticate_user(email, password)
        if user:
            remember = bool(request.form.get("remember_me"))
            login_user(user, remember=remember)
            flash("Welcome back.", "success")
            return redirect(url_for("main.dashboard_user"))

        flash("Invalid credentials or inactive account.", "danger")
    return render_template("Auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard_user"))

    if request.method == "POST":
        full_name = (
            (request.form.get("full_name") or "").strip()
            or (request.form.get("name") or "").strip()
        )
        if not full_name:
            first_name = (request.form.get("first_name") or "").strip()
            last_name = (request.form.get("last_name") or "").strip()
            full_name = f"{first_name} {last_name}".strip()

        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""
        selected_role = (request.form.get("role") or "").strip().lower()
        if selected_role not in {"user", "provider"}:
            selected_role = "user"
        is_provider = selected_role == "provider"
        role = "provider" if is_provider else "user"
        main_category = (request.form.get("main_category") or "").strip().lower()
        subcategory = (request.form.get("subcategory") or "").strip().lower()
        business_name = (request.form.get("business_name") or "").strip()

        if not email:
            flash("Email is required.", "danger")
            return render_template("Auth/register.html")
        if not password:
            flash("Password is required.", "danger")
            return render_template("Auth/register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("Auth/register.html")
        if confirm_password and password != confirm_password:
            flash("Password confirmation does not match.", "danger")
            return render_template("Auth/register.html")
        if is_provider:
            if not business_name:
                flash("Business name is required for provider registration.", "danger")
                return render_template("Auth/register.html")
            if not main_category:
                flash("Main category is required for provider registration.", "danger")
                return render_template("Auth/register.html")
            allowed_subcategories = PROVIDER_SUBCATEGORIES.get(main_category, set())
            if not subcategory:
                flash("Subcategory is required for provider registration.", "danger")
                return render_template("Auth/register.html")
            if allowed_subcategories and subcategory not in allowed_subcategories:
                flash("Selected subcategory is not valid for that main category.", "danger")
                return render_template("Auth/register.html")

        try:
            user = create_user(
                full_name=full_name,
                email=email,
                password=password,
                role=role,
                main_category=main_category if is_provider else None,
                subcategory=subcategory if is_provider else None,
                business_name=business_name if is_provider else None,
            )
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("Auth/register.html")
        except SQLAlchemyError:
            flash("Could not create account right now. Please try again.", "danger")
            return render_template("Auth/register.html")

        login_user(user)
        flash("Account created successfully.", "success")
        return redirect(url_for("main.dashboard_user"))

    return render_template("Auth/register.html")

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Password recovery is not enabled yet. Contact support.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("Auth/forgot_password.html")


@auth_bp.route("/logout", methods=["GET"])
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
