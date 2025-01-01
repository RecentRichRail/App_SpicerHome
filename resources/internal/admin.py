from flask import Blueprint, request, current_app, render_template, abort
from models import db, User, RequestsModel, TrackingNumbersModel
from flask_login import login_required, current_user
from sqlalchemy import or_

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
    query = request.args.get('q', '').lower()

    results = User.query.filter(
        or_(
            User.uid.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        )
    ).limit(5).all()
    
    return render_template('/internal/admin/partials/admin_user_search_suggestions.html', results=results)