from flask import Blueprint, request, render_template
from flask_login import login_required, current_user
from models import ChoresUser, db, User, ChoreRequest, PointsRequest
from datetime import datetime
import logging

chores_blueprint = Blueprint("chores", __name__, template_folder="templates/internal/chores")

@chores_blueprint.route('/', methods=['GET'])
@login_required
def view_points():
    
    all_users_points = {}
    if current_user.is_household_admin():
        choreusers = ChoresUser.query.filter_by(household_id=current_user.is_in_household(), household_admin=False).all()
        last_25_requests = ChoreRequest.query.filter_by(household_id=current_user.is_in_household()).order_by(ChoreRequest.request_created_at.desc()).limit(25).all()
        open_requests = ChoreRequest.query.filter_by(household_id=current_user.is_in_household(), is_request_active=True, request_cancelled_at=None).order_by(ChoreRequest.request_created_at.desc()).all()
        available_requests = PointsRequest.query.filter_by(household_id=current_user.is_in_household(), is_request_active=True).all()
        all_users_points = {}
        for user in choreusers:
            user_model = User.query.filter_by(id=user.user_id).first()
            if user_model and user_model.name:  # Ensure user_model and user_model.name are not None
                all_users_points[user_model.id] = {"name": user_model.name, "amount": int(user.dollar_amount)}
    else:
        last_25_requests = ChoreRequest.query.filter_by(household_id=current_user.is_in_household(), request_created_for_user_id=current_user.id).order_by(ChoreRequest.request_created_at.desc()).limit(25).all()
        available_requests = PointsRequest.query.filter_by(household_id=current_user.is_in_household(), is_request_active=True).all()
                
  
    page_title = "SpicerHome Points"

    if current_user.is_household_admin():
        context = {
            'page_title': page_title,
            'all_users_points': all_users_points,
            'last_25_requests': last_25_requests,
            'open_requests': open_requests,
            'available_requests': available_requests
        }
    else:
        context = {
                    'page_title': page_title,
                    'all_users_points': all_users_points,
                    'last_25_requests': last_25_requests,
                    'available_requests': available_requests
                }
    
    return render_template('internal/chores/choresbase.html', **context)

@chores_blueprint.route('/points', methods=['GET'])
@login_required
def points():
    choreuser = ChoresUser.query.filter_by(user_id=current_user.id).first()
    if not choreuser:
        return {"message": "User not found"}, 404

    if current_user.is_household_admin():  # Assuming you have a way to check if the user is an admin
        choreusers = ChoresUser.query.filter_by(household_id=current_user.is_in_household(), household_admin=False).all()
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
    reason = data.get('reason')

    if not user_ids or not isinstance(user_ids, list):
        return {"message": "Invalid user IDs"}, 400

    if reason:
        reason = f", Reason: {reason}"
    else:
        reason = "."

    updated_users = []
    for user_id in user_ids:
        user = ChoresUser.query.filter_by(user_id=user_id).first()
        user_model = User.query.filter_by(id=user.user_id).first()
        if not user:
            return {"message": f"User with ID {user_id} not found"}, 404

        user_model = User.query.filter_by(id=user.user_id).first()

        if action == 'add':
            display_points = amount
            user.dollar_amount += amount
            if amount == 1:
                request_reason_created=f"{current_user.name} {action}ed {amount} point to {user_model.name}{reason}"
            else:
                request_reason_created=f"{current_user.name} {action}ed {amount} points to {user_model.name}{reason}"
        elif action == 'subtract':
            display_points = -amount
            user.dollar_amount -= amount
            if amount == 1:
                request_reason_created=f"{current_user.name} {action}ed {amount} point from {user_model.name}{reason}"
            else:
                request_reason_created=f"{current_user.name} {action}ed {amount} points from {user_model.name}{reason}"
        else:
            return {"message": "Invalid action"}, 400

        updated_users.append({"id": user_id, "name": user_model.name, "amount": user.dollar_amount})

        # Log the points request
        chore_request = ChoreRequest(
            request_created_by_user_id=current_user.id,
            request_created_for_user_id=user_id,
            requested_point_amount_requested=display_points,
            household_id=user.household_id,
            request_reason_created=request_reason_created,
            is_request_active=False,
            request_fulfilled_at = datetime.utcnow(),
            request_fulfilled_by = current_user.id
        )
        db.session.add(chore_request)

    db.session.commit()
    
    response = render_template('internal/chores/partials/update_points_feedback.html', updated_users=updated_users, action=action, amount=amount)
    response += '<script>refreshLatestRequestLogs();</script>'
    
    return response

@chores_blueprint.route('/latest_request_logs', methods=['GET'])
@login_required
def latest_request_logs_partial():
    if current_user.is_household_admin():
        last_25_requests = ChoreRequest.query.filter_by(household_id=current_user.is_in_household()).order_by(ChoreRequest.request_created_at.desc()).limit(25).all()
    else:
        last_25_requests = ChoreRequest.query.filter_by(household_id=current_user.is_in_household(), request_created_for_user_id=current_user.id).order_by(ChoreRequest.request_created_at.desc()).limit(25).all()

    return render_template('internal/chores/partials/latest_request_logs.html', last_25_requests=last_25_requests)

@chores_blueprint.route('/approve_request/<int:request_id>', methods=['POST'])
@login_required
def approve_request(request_id):
    chore_request = ChoreRequest.query.get(request_id)
    chore_user_model = ChoresUser.query.filter_by(user_id=chore_request.request_created_for_user_id).first()
    if not chore_request or not current_user.is_household_admin():
        return {"message": "Request not found or permission denied"}, 404

    chore_request.is_request_active = False
    chore_request.request_fulfilled_at = datetime.utcnow()
    chore_request.request_fulfilled_by = current_user.id

    chore_user_model.dollar_amount += chore_request.requested_point_amount_requested

    db.session.commit()

    return render_template('internal/chores/partials/request_approved.html', request=chore_request)

@chores_blueprint.route('/deny_request/<int:request_id>', methods=['POST'])
@login_required
def deny_request(request_id):
    chore_request = ChoreRequest.query.get(request_id)
    if not chore_request or not current_user.is_household_admin():
        return {"message": "Request not found or permission denied"}, 404

    chore_request.is_request_active = False
    chore_request.request_cancelled_at = datetime.utcnow()
    chore_request.requst_cancelled_by = current_user.id

    db.session.commit()

    return render_template('internal/chores/partials/request_denied.html', request=chore_request)

@chores_blueprint.route('/request_points', methods=['POST'])
@login_required
def request_points():
    choreuser = ChoresUser.query.filter_by(user_id=current_user.id).first()
    if not choreuser:
        return {"message": "User not found"}, 404
    
    if request.method == 'POST':
        request_id = request.args.get('id')
        request_for = request.args.get('for')
        request_for_name = User.query.filter_by(id=request_for).first().name
        request_model = PointsRequest.query.filter_by(household_id=current_user.is_in_household(), is_request_active=True, id=request_id).first()
        request_reason_created = f"{request_for_name} requested {request_model.points_requested} points for {request_model.request_name}."
        today = datetime.utcnow().date()
        todays_similar_requests = ChoreRequest.query.filter(
            ChoreRequest.household_id == current_user.is_in_household(),
            ChoreRequest.request_created_for_user_id == request_for,
            ChoreRequest.request_reason_created == request_reason_created,
            db.func.date(ChoreRequest.request_created_at) == today
        ).order_by(ChoreRequest.request_created_at.desc()).all()

        if todays_similar_requests and len(todays_similar_requests) + 1 > request_model.daily_limit:
            logging.debug(f"len(todays_similar_requests): {len(todays_similar_requests)}")
            logging.debug(f"Daily Limit: {request_model.daily_limit}")
            status = f"Daily Limit Reached for {request_for_name}"
            if current_user.is_household_admin():
                return status
            else:
                return render_template('internal/chores/partials/user_request_feedback.html', status=status, available_request=request_model.to_dict())
            
        logging.debug(f"len(todays_similar_requests): {len(todays_similar_requests)}")
        logging.debug(f"Daily Limit: {request_model.daily_limit}")
        
        chore_request = ChoreRequest(
            request_created_by_user_id=current_user.id,
            request_created_for_user_id=request_for,
            requested_point_amount_requested=request_model.points_requested,
            household_id=choreuser.household_id,
            request_reason_created=request_reason_created,
            is_request_active=True
        )
        db.session.add(chore_request)

        db.session.commit()
        status = f"Request Created for {request_for_name}"

        if current_user.is_household_admin():
            approve_request(chore_request.id)
            return status
        
        return render_template('internal/chores/partials/user_request_feedback.html', status=status, available_request=request_model.to_dict())