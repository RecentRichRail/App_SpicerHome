from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import ChoresUser, db, User, ChoreRequest, PointsRequest, Household, HouseholdJoinRequest
from datetime import datetime
from sqlalchemy import and_
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
    
    household = Household.query.filter_by(id=current_user.is_in_household()).first()
    users = ChoresUser.query.filter(and_(ChoresUser.household_id == current_user.is_in_household(), ChoresUser.user_id != current_user.id)).all()
    return render_template('internal/household/householdbase.html', household=household, users=users)

@household_blueprint.route('/search_user')
@login_required
def household_search_user():
    if current_user.is_household_admin():
        query = request.args.get('q', '').lower()

        user_result = User.query.filter_by(uid = query).filter(~User.household.any()).limit(5).all()

        return render_template('/internal/household/partials/household_user_search_suggestions.html', results=user_result)
    else:
        return redirect(url_for('household.manage_household'))
    
@household_blueprint.route('/request_user_to_household', methods=['POST'])
@login_required
def request_user_to_household():
    if current_user.is_household_admin():
        logging.debug("Requesting user to household.")
        requested_user_uid = request.json.get('user_uid')
        logging.debug(f"Requested user UID: {requested_user_uid}")
        household_id = current_user.is_in_household()
        household_admin = current_user.id

        requested_user = User.query.filter_by(uid=requested_user_uid).first()
        if not requested_user:
            logging.debug(f"User not found. {requested_user_uid}")
            return "User not found.", 404

        if not requested_user_uid or not household_id:
            logging.debug("User ID and Household ID are required.")
            return "User ID and Household ID are required.", 400

        household = Household.query.filter_by(id=household_id).first()
        if not household:
            logging.debug("Household not found.")
            return "Household not found.", 404

        household_user = ChoresUser.query.filter_by(user_id=requested_user.id).first()
        if household_user:
            logging.debug("User is already in the household.")
            return "User is already in the household.", 400
        
        pending_request = HouseholdJoinRequest.query.filter_by(request_created_for_user_id=requested_user.id, is_request_active=True).first()
        if pending_request:
            logging.debug("User already has a request pending.")
            return "User already has a request pending.", 400

        join_request = HouseholdJoinRequest.create_request(household_admin, requested_user.id, household_id)
        db.session.add(join_request)
        db.session.commit()
        return "User added to household.", 200
    else:
        return redirect(url_for('household.manage_household'))
    
@household_blueprint.route('/make_household_admin', methods=['POST'])
@login_required
def make_household_admin():
    if current_user.is_household_admin():
        user_id = request.json.get('user_id')
        user = ChoresUser.query.filter_by(user_id=user_id).first()
        if not user:
            return "User not found.", 404
        user.make_household_admin()
        return "User is now a household admin.", 200
    else:
        return redirect(url_for('household.manage_household'))
    
@household_blueprint.route('/approve_request', methods=['POST'])
@login_required
def approve_household_request():
    request_id = request.json.get('request_id')
    if not current_user.is_household_admin():
        # request_id = request.json.get('request_id')
        request_model = HouseholdJoinRequest.query.filter_by(id=request_id, request_created_for_user_id=current_user.id).first()
        if not request_model:
            return "Request not found.", 404

        request_model.approve_request(request_fulfilled_by=current_user.id)
        return "Request approved.", 200
    else:
        return redirect(url_for('household.manage_household'))
    
@household_blueprint.route('/deny_request', methods=['POST'])
@login_required
def deny_household_request():
    if not current_user.is_household_admin():
        request_id = request.json.get('request_id')
        request_model = HouseholdJoinRequest.query.filter_by(id=request_id, request_created_for_user_id=current_user.id).first()
        if not request_model:
            return "Request not found.", 404

        request_model.deny_request(request_cancelled_by=current_user.id)
        return "Request denied.", 200
    else:
        return redirect(url_for('household.manage_household'))