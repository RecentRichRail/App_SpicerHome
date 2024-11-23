from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import ChoresUser, db, PermissionsModel, Household, User

chores_blueprint = Blueprint("chores", __name__, template_folder="templates/internal/chores")

@chores_blueprint.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('internal/chores/dashboard.html')

@chores_blueprint.route('/points', methods=['GET'])
@login_required
def view_points():
    user = ChoresUser.query.filter_by(name=current_user.username).first()
    if not user:
        return {"message": "User not found"}, 404
    return render_template('internal/chores/view_points.html')

@chores_blueprint.route('/manage_points', methods=['GET', 'POST'])
@login_required
def manage_points():
    if request.method == 'GET':
        return render_template('internal/chores/manage_points.html')

    data = request.get_json()
    username = data.get('username')
    action = data.get('action')
    amount = data.get('amount')

    user_permissions = PermissionsModel.query.filter_by(user_id=current_user.id).first()
    if not user_permissions or user_permissions.permission_level < 2:
        return {"message": "Permission denied"}, 403

    user = ChoresUser.query.filter_by(name=username).first()
    if not user:
        return {"message": "User not found"}, 404

    if action == 'add':
        user.dollar_amount += amount
    elif action == 'subtract':
        user.dollar_amount -= amount
    else:
        return {"message": "Invalid action"}, 400

    db.session.commit()
    return {"message": "Points updated successfully"}

@chores_blueprint.route('/create_household', methods=['GET', 'POST'])
@login_required
def create_household():
    if request.method == 'GET':
        return render_template('internal/chores/manage_households.html')

    data = request.get_json()
    name = data.get('name')

    if not name:
        return {"message": "Household name is required"}, 400

    household = Household(name=name, owner_id=current_user.id)
    db.session.add(household)
    db.session.commit()

    return {"message": "Household created successfully", "household_id": household.id}, 201

@chores_blueprint.route('/manage_households', methods=['GET'])
@login_required
def manage_households():
    return render_template('internal/chores/manage_households.html')

@chores_blueprint.route('/add_members', methods=['POST'])
@login_required
def add_members():
    data = request.get_json()
    household_id = data.get('household_id')
    member_emails = data.get('member_emails')

    if not household_id or not member_emails:
        return {"message": "Household ID and Member Emails are required"}, 400

    household = Household.query.get(household_id)
    if not household:
        return {"message": "Household not found"}, 404

    if household.owner_id != current_user.id:
        return {"message": "Only the household owner can add members"}, 403

    for email in member_emails:
        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": f"User with email {email} not found"}, 404

        chores_user = ChoresUser.query.filter_by(name=user.username).first()
        if not chores_user:
            chores_user = ChoresUser(name=user.username, dollar_amount=0.0, household_id=household_id)
            db.session.add(chores_user)
        else:
            chores_user.household_id = household_id

    db.session.commit()
    return {"message": "Members added successfully"}, 200

@chores_blueprint.route('/add_admins', methods=['POST'])
@login_required
def add_admins():
    data = request.get_json()
    household_id = data.get('household_id')
    admin_emails = data.get('admin_emails')

    if not household_id or not admin_emails:
        return {"message": "Household ID and Admin Emails are required"}, 400

    household = Household.query.get(household_id)
    if not household:
        return {"message": "Household not found"}, 404

    if household.owner_id != current_user.id:
        return {"message": "Only the household owner can add admins"}, 403

    for email in admin_emails:
        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": f"User with email {email} not found"}, 404

        chores_user = ChoresUser.query.filter_by(name=user.username).first()
        if not chores_user:
            chores_user = ChoresUser(name=user.username, dollar_amount=0.0, household_id=household_id, household_admin=True)
            db.session.add(chores_user)
        else:
            chores_user.household_id = household_id
            chores_user.household_admin = True

    db.session.commit()
    return {"message": "Admins added successfully"}, 200