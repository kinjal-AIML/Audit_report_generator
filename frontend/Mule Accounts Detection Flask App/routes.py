from flask import Blueprint, render_template
from datetime import datetime

main = Blueprint('main', __name__)

@main.route("/")
def home():
    return render_template("base.html", current_year=datetime.now().year)