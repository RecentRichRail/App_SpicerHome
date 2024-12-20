from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import ChoresUser, db, PermissionsModel, Household, User

chores_blueprint = Blueprint("chores", __name__, template_folder="templates/internal/chores")

# @chores_blueprint.route('/dashboard', methods=['GET'])
# @login_required
# def dashboard():
#     return render_template('internal/chores/dashboard.html')

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
                all_users_points[user_model.id] = {"name": user_model.name, "amount": user.dollar_amount}
    # else:
    #     user_points = {choreuser.user_id: {"name": current_user.name, "amount": choreuser.dollar_amount}}

    page_title = "SpicerHome Points"

    context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links(),
                'all_users_points': all_users_points
                # 'cookie_name': current_app.short_session_cookie_name
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
                all_users_points[user_model.id] = {"name": user_model.name, "amount": user.dollar_amount}
        return {"message": "success", "points": all_users_points, "is_admin": True}, 200
    else:
        return {"message": "success", "points": {choreuser.user_id: {"name": current_user.name, "amount": choreuser.dollar_amount}}, "is_admin": False}, 200

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

# @chores_blueprint.route('/create_household', methods=['GET', 'POST'])
# @login_required
# def create_household():
#     if request.method == 'GET':
#         return render_template('internal/chores/manage_households.html')

#     data = request.get_json()
#     name = data.get('name')

#     if not name:
#         return {"message": "Household name is required"}, 400

#     household = Household(name=name, owner_id=current_user.id)
#     db.session.add(household)
#     db.session.commit()

#     return {"message": "Household created successfully", "household_id": household.id}, 201

# @chores_blueprint.route('/manage_households', methods=['GET'])
# @login_required
# def manage_households():
#     return render_template('internal/chores/manage_households.html')

# @chores_blueprint.route('/add_members', methods=['POST'])
# @login_required
# def add_members():
#     data = request.get_json()
#     household_id = data.get('household_id')
#     member_emails = data.get('member_emails')

#     if not household_id or not member_emails:
#         return {"message": "Household ID and Member Emails are required"}, 400

#     household = Household.query.get(household_id)
#     if not household:
#         return {"message": "Household not found"}, 404

#     if household.owner_id != current_user.id:
#         return {"message": "Only the household owner can add members"}, 403

#     for email in member_emails:
#         user = User.query.filter_by(email=email).first()
#         if not user:
#             return {"message": f"User with email {email} not found"}, 404

#         chores_user = ChoresUser.query.filter_by(name=user.username).first()
#         if not chores_user:
#             chores_user = ChoresUser(name=user.username, dollar_amount=0.0, household_id=household_id)
#             db.session.add(chores_user)
#         else:
#             chores_user.household_id = household_id

#     db.session.commit()
#     return {"message": "Members added successfully"}, 200

# @chores_blueprint.route('/add_admins', methods=['POST'])
# @login_required
# def add_admins():
#     data = request.get_json()
#     household_id = data.get('household_id')
#     admin_emails = data.get('admin_emails')

#     if not household_id or not admin_emails:
#         return {"message": "Household ID and Admin Emails are required"}, 400

#     household = Household.query.get(household_id)
#     if not household:
#         return {"message": "Household not found"}, 404

#     if household.owner_id != current_user.id:
#         return {"message": "Only the household owner can add admins"}, 403

#     for email in admin_emails:
#         user = User.query.filter_by(email=email).first()
#         if not user:
#             return {"message": f"User with email {email} not found"}, 404

#         chores_user = ChoresUser.query.filter_by(name=user.username).first()
#         if not chores_user:
#             chores_user = ChoresUser(name=user.username, dollar_amount=0.0, household_id=household_id, household_admin=True)
#             db.session.add(chores_user)
#         else:
#             chores_user.household_id = household_id
#             chores_user.household_admin = True

#     db.session.commit()
#     return {"message": "Admins added successfully"}, 200