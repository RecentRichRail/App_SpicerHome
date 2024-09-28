from flask import Blueprint, request, current_app, render_template
from models import User, RequestsModel, TrackingNumbersModel, LoginAttemptModel
from flask_login import login_user, login_required, current_user, logout_user
from models import db

# import requests

from tracking_numbers import get_tracking_number

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route('/')
@login_required
def admin_history():
    user_id = request.args.get('q')
    selected_info = request.args.get('info')
    # data = current_app.data
    if selected_info == "history":
        for permission in current_user.permissions:
            if permission.permission_name == "admin" and permission.permission_level == 0:

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
            else:
                response = {"message": "No permission for this resource."}
        
        history_requests = response
        page_title = f"SpicerHome {user_id} History"

        context = {
                'history_requests': history_requests,
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
            }

        return render_template('internal/search/history.html', **context)
    
    elif selected_info == "track":
        for permission in current_user.permissions:
            if permission.permission_name == "admin" and permission.permission_level == 0:

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
            else:
                response = {"message": "No permission for this resource."}
        
        tracking_requests = response
        page_title = f"SpicerHome {user_id} Tracking"

        context = {
                'tracking_requests': tracking_requests,
                # 'users_query': users_query,
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
            }

        return render_template('internal/search/tracking.html', **context)
    
    else:
        for permission in current_user.permissions:
            if permission.permission_name == "admin" and permission.permission_level == 0:

                admin_users_query = User.query.order_by(User.id.desc()).all()

                admin_user_query_structured = {}
                for user in admin_users_query:
                    admin_user_query_structured[user.id] = user.to_dict()

                print(admin_user_query_structured)
                response = admin_user_query_structured
            else:
                response = {"message": "No permission for this resource."}
        users_query = response
        print(users_query)

        # response = requests.post(f"http://{current_app.mysql_database_api}/apiv1/admin/user/login/requests_unauth", json={"data": data})
        # login_request_query = response.json()
        # print(login_request_query)
        page_title = f"SpicerHome Admin Portal"

        context = {
                # 'login_request_query': login_request_query,
                'users_query': users_query,
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
            }

        return render_template('admin/admin_index.html', **context)