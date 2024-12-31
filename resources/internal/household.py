from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from models import ChoresUser, db, User, ChoreRequest, PointsRequest, Household
from datetime import datetime
import logging

household_blueprint = Blueprint("household", __name__, template_folder="templates/internal/household")

@household_blueprint.route('/create_household', methods=['POST'])
@login_required
def create_household():
    household_name = request.form.get('household_name')

    if not household_name:
        return "Household name is required.", 400

    household = Household.create_household(str(household_name), current_user.id)
    if household:
        return render_template('internal/household/partials/created_household.html', household=household)
    else:
        return "Household creation failed.", 500