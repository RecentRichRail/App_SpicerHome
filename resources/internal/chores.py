from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import ChoresUser, db, PermissionsModel, Household, User

chores_blueprint = Blueprint("chores", __name__, template_folder="templates/internal/chores")

@chores_blueprint.route('/', methods=['GET'])
@login_required
def view_points():
    
    all_users_points = {}
    if current_user.is_household_admin():
        choreusers = ChoresUser.query.filter_by(household_admin=False).all()
        all_users_points = {}
        for user in choreusers:
            user_model = User.query.filter_by(id=user.user_id).first()
            if user_model and user_model.name:  # Ensure user_model and user_model.name are not None
                all_users_points[user_model.id] = {"name": user_model.name, "amount": int(user.dollar_amount)}
  
    page_title = "SpicerHome Points"

    context = {
                'page_title': page_title,
                'all_users_points': all_users_points
            }
    
    return render_template('internal/chores/choresbase.html', **context)

@chores_blueprint.route('/points', methods=['GET'])
@login_required
def points():
    choreuser = ChoresUser.query.filter_by(user_id=current_user.id).first()
    if not choreuser:
        return {"message": "User not found"}, 404

    if current_user.is_household_admin():  # Assuming you have a way to check if the user is an admin
        choreusers = ChoresUser.query.filter_by(household_admin=False).all()
        all_users_points = {}
        for user in choreusers:
            user_model = User.query.filter_by(id=user.user_id).first()
            if user_model and user_model.name:  # Ensure user_model and user_model.name are not None
                all_users_points[user_model.id] = {"name": user_model.name, "amount": int(user.dollar_amount)}
        return {"message": "success", "points": all_users_points, "is_admin": True}, 200
    else:
        return {"message": "success", "points": {choreuser.user_id: {"name": current_user.name, "amount": int(choreuser.dollar_amount)}}, "is_admin": False}, 200

@chores_blueprint.route('/manage_points', methods=['POST'])
@login_required
def update_points():

    if not current_user.is_household_admin():
        return {"message": "Permission denied"}, 404

    if request.content_type != 'application/json':
        return {"message": "Content-Type must be application/json"}, 415

    data = request.get_json()
    user_ids = data.get('user_ids')
    action = data.get('action')
    amount = int(data.get('amount'))

    if not user_ids or not isinstance(user_ids, list):
        return {"message": "Invalid user IDs"}, 400

    updated_users = []
    for user_id in user_ids:
        user = ChoresUser.query.filter_by(user_id=user_id).first()
        if not user:
            return {"message": f"User with ID {user_id} not found"}, 404

        if action == 'add':
            user.dollar_amount += amount
        elif action == 'subtract':
            user.dollar_amount -= amount
        else:
            return {"message": "Invalid action"}, 400
        
        user_model = User.query.filter_by(id=user.user_id).first()

        updated_users.append({"id": user_id, "name": user_model.name, "amount": user.dollar_amount})

    db.session.commit()
    return render_template('internal/chores/partials/update_points_feedback.html', updated_users=updated_users, action=action, amount=amount)