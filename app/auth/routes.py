from flask import render_template, redirect, url_for, flash, request
from . import auth_bp

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        flash("Login flow pending Supabase Auth integration.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        flash("Register flow pending Supabase Auth integration.", "info")
        return redirect(url_for("auth.register"))
    return render_template("auth/register.html")

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("Forgot password flow pending Supabase Auth integration.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("auth/forgot_password.html")