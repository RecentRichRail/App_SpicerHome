from flask import Blueprint, render_template

external_blueprint = Blueprint("external", __name__, template_folder="templates")


@external_blueprint.route("/test")
def index():
    # Hello World!
    return render_template("external/test.html")