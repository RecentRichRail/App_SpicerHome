from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import ChoresUser, db, User, ChoreRequest, PointsRequest, Household
from datetime import datetime
from sqlalchemy import or_
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
        household.add_user_to_household(current_user.id, True)
        return render_template('internal/household/partials/created_household.html', household=household)
    else:
        return "Household creation failed.", 500
    
# make a portal for the household admins to manage the household
@household_blueprint.route('/manage_household', methods=['GET'])
@login_required
def manage_household():
    household_admin = ChoresUser.query.filter_by(user_id=current_user.id, household_admin=True).first()
    if not household_admin:
        household_member = ChoresUser.query.filter_by(user_id=current_user.id).first()
        if household_member:
            return "You are not a household admin.", 400
        else:
            return redirect(url_for('internal.user_settings'))
    
    household = Household.query.filter_by(owner_id=current_user.id).first()
    return render_template('internal/household/householdbase.html', household=household)

@household_blueprint.route('/search_user')
@login_required
def household_search_user():
    if current_user.is_household_admin():
        query = request.args.get('q', '').lower()

        user_result = User.query.filter(User.uid.ilike(f"%{query}%")).filter(~User.household.any()).limit(5).all()

        return render_template('/internal/household/partials/household_user_search_suggestions.html', results=user_result)
    else:
        return redirect(url_for('household.manage_household'))