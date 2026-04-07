from . import main_bp
from flask import render_template

@main_bp.route("/")
def home():
    return render_template("pages/home-1.html")