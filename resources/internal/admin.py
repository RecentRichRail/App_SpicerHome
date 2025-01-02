from flask import Blueprint, request, current_app, render_template, abort
from models import db, User, RequestsModel, TrackingNumbersModel, CommandsModel
from flask_login import login_required, current_user
from sqlalchemy import or_
import logging

# import requests

from tracking_numbers import get_tracking_number

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route('/')
@login_required
def admin_history():
    user_id = request.args.get('q')
    selected_info = request.args.get('info')
    # data = current_app.data
    admin_permission = next((perm for perm in current_user.json_user_permissions() if perm["permission_name"] == "admin" and perm["permission_level"] == 0), None)
    if not admin_permission:
        abort(404)
    if selected_info == "history":

        admin_history_query = RequestsModel.query.filter_by(user_id=user_id).order_by(RequestsModel.id.desc()).all()

        admin_history_query_structured = {user_id: {}}
        for history_request in admin_history_query:
            if history_request.is_search == True:
                try:
                    user_query_url = history_request.command.search_url.format(history_request.encoded_query)
                except AttributeError:
                    user_query_url = history_request.command.url
            elif history_request.is_search == False:
                user_query_url = history_request.command.url

            admin_history_query_structured[user_id][history_request.id] = {
                "request_id": history_request.id,
                "original_request": history_request.original_request,
                "query_url": user_query_url,
                "date_and_time": history_request.datetime_of_request
            }
        response = admin_history_query_structured

        history_requests = response
        page_title = f"SpicerHome {user_id} History"

        context = {
                'history_requests': history_requests,
                'page_title': page_title
            }

        return render_template('internal/search/history.html', **context)
    
    elif selected_info == "track":


        user_track_query = TrackingNumbersModel.query.filter_by(user_id=user_id).order_by(TrackingNumbersModel.id.desc()).all()

        user_track_query_structured = {user_id: {}}
        for track_request in user_track_query:
            tracking = get_tracking_number(track_request.tracking_number)
            user_track_query_structured[user_id][track_request.id] = {
                "track_id": track_request.id,
                "tracking_number": track_request.tracking_number,
                "query_url": tracking.tracking_url,
                "courier_name": tracking.courier.name,
                "note": track_request.note,
                "is_active": track_request.is_active,
                "datetime_of_create_on_database": track_request.datetime_of_create_on_database
            }
        response = user_track_query_structured

        tracking_requests = response
        page_title = f"SpicerHome {user_id} Tracking"

        context = {
                'tracking_requests': tracking_requests,
                'page_title': page_title
            }

        return render_template('internal/search/tracking.html', **context)
    
    else:
        admin_users_query = User.query.order_by(User.id.desc()).all()
        admin_user_query_structured = {}
        for user in admin_users_query:
            admin_user_query_structured[user.id] = user.to_dict()
        response = admin_user_query_structured
        users_query = response
        print(f" users = {users_query}")

        page_title = f"SpicerHome Admin Portal"

        context = {
            'users_query': users_query,
            'page_title': page_title
        }

        return render_template('/internal/admin/adminbase.html', **context)

@admin_blueprint.route('/search_user')
@login_required
def search_user():
    admin_permission = next((perm for perm in current_user.json_user_permissions() if perm["permission_name"] == "admin" and perm["permission_level"] == 0), None)
    if not admin_permission:
        abort(404)
    query = request.args.get('q', '').lower()
    logging.info(f"search_user query = {query}")

    results = User.query.filter(
        or_(
            User.username.ilike(f'%{query}%'),
            User.name.ilike(f'%{query}%'),
            User.uid.ilike(f'%{query}%'),
            User.id.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        )
    ).limit(5).all()
    
    return render_template('/internal/admin/partials/admin_user_search_suggestions.html', results=results)

@admin_blueprint.route('/create_command', methods=['POST'])
@login_required
def create_command():
    admin_permission = next((perm for perm in current_user.json_user_permissions() if perm["permission_name"] == "admin" and perm["permission_level"] == 0), None)
    if not admin_permission:
        abort(404)
    category = request.json.get('category')
    if category == "":
        abort(400)
    prefix = request.json.get('prefix')
    if prefix == "":
        abort(400)
    url = request.json.get('url')
    if url == "":
        abort(400)
    search_url = request.json.get('search_url', None)
    if search_url == "":
        search_url = None
    permission_name = request.json.get('permission_name', 'commands')
    if permission_name == "":
        permission_name = 'commands'
    permission_level = request.json.get('permission_level', 999)
    if permission_level == "":
        permission_level = 999
    is_command_for_sidebar = request.json.get('is_command_for_sidebar', False)
    if is_command_for_sidebar == 'True' or is_command_for_sidebar == 'on':
        is_command_for_sidebar = True
    else:
        is_command_for_sidebar = False
    is_command_public = request.json.get('is_command_public', True)
    if is_command_public == 'True' or is_command_public == 'on':
        is_command_public = True
    else:
        is_command_public = False
    is_command_household = request.json.get('is_command_household', False)
    if is_command_household == 'True' or is_command_household == 'on':
        is_command_household = True
    else:
        is_command_household = False
    is_command_hidden = request.json.get('is_command_hidden', False)
    if is_command_hidden == 'True' or is_command_hidden == 'on':
        is_command_hidden = True
    else:
        is_command_hidden = False
    household_id = request.json.get('household_id', None)
    if household_id == "":
        household_id = None
    owner_id = request.json.get('owner_id', current_user.id)
    if owner_id == "":
        owner_id = None
    
    new_command = CommandsModel.create_command(
        category=category,
        prefix=prefix,
        url=url,
        search_url=search_url,
        permission_name=permission_name,
        permission_level=permission_level,
        is_command_for_sidebar=is_command_for_sidebar,
        is_command_public=is_command_public,
        is_command_household=is_command_household,
        is_command_hidden=is_command_hidden,
        household_id=household_id,
        owner_id=owner_id
    )
    if new_command:
        return new_command.to_dict(), 201
    
    return "Command failed to create.", abort(500)