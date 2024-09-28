from flask import Blueprint, render_template, current_app, redirect, request
from flask_login import login_user, login_required, current_user, logout_user
import requests
import importlib
import os
from tracking_numbers import get_tracking_number

import datetime

from models import TrackingNumbersModel, RequestsModel

from flask import (
    Blueprint,
    render_template,
    request,
    make_response,
    session,
    abort,
    url_for,
    redirect,
    flash,
)
import base64
# import Response
from flask_login import login_user, login_required, current_user, logout_user
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from webauthn.helpers.exceptions import (
    InvalidRegistrationResponse,
    InvalidAuthenticationResponse,
)
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential

from resources.utils import security, util, search_utils

internal_blueprint = Blueprint("internal", __name__, template_folder="templates")

# import urllib.parse
# from brave import Brave

blp = internal_blueprint

def run_funtion(script_path, data):
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run(data)

def user_search_query(offset, search_query):
    # data = request.get_json()
    # print(f"Data received: {data}")
    search_query_prefix = search_query.split(' ')[0].lower()

    data = [current_user, search_query_prefix, search_query, offset]

    # Should be how the data looks:
    # data = {'user_query': {'prefix': 'yellow', 'original_request': 'yellow cab'}, 'user_info': {'user_id': 'ID12345'}}
    # After tracking.py:
    # data = {'user_query': {'original_request': 'yellow cab', 'prefix': 'yellow'}, 'user_info': {'user_id': 'ID12345'}, 'tracking_details': None}

    for filename in os.listdir('resources/utils/functions'):
        if filename.endswith('.py') and filename != 'search.py':
            print(f"Running {filename}")
            script_path = os.path.join('resources/utils/functions', filename)
            try:
                script_return = run_funtion(script_path, data)
                if script_return.get("funtion_triggered"):
                    return {"internal_search": script_return.get("internal_search", False), "function_data": script_return['funtion_return']}
            except Exception as e:
                print(f"Error running {filename}: {e}")
                return {"error": str(e)}
            
    print(f"Running 'search.py'")
    script_path = os.path.join('resources/utils/functions', 'search.py')
    try:
        script_return = run_funtion(script_path, data)
        # print(f"script_return: {script_return}")
        if script_return.get("funtion_triggered"):
            return {"internal_search": script_return.get("internal_search", False), "function_data": script_return['funtion_return']}
    except Exception as e:
                print(f"Error running search.py: {e}")
                return {"error": str(e)}
    # print({"redirect_url": run_funtion(os.path.join('resources/functions', 'search.py'), data)['funtion_return']})
    return {"internal_search": script_return.get("internal_search", False), "function_data": run_funtion(os.path.join('resources/utils/functions', 'search.py'), data)['funtion_return']}


@blp.route('/search')
@login_required
def internal_search():
    # if request.args.get('query'):
    #     user_query = request.args.get('query')
    user_query = request.args.get('q')
    offset = request.args.get('offset', '0')
    # print(f"user_query = {user_query}")

    # data = current_app.data
    
    if user_query:
        # data['user_query'] = {'original_request': user_query}
        # data['user_query']['offset'] = offset
        
        # Redirect based on search query
        # if not user_query:
            # print(f"No user_query - {user_query}")
            # return redirect('/')

        response = user_search_query(offset, user_query)
        
        # response = requests.post(f"http://{current_app.mysql_database_api}/apiv1/search/query", json=data)
        # response = response.json()
        
        print(response)

        # try:
        #     if response['internal_search']:
        #         search_index = response['function_data']
        #         page_title = "SpicerHome Search"
        # except KeyError:
        #     return redirect(response['function_data'])

        if not response['internal_search']:
            return redirect(response['function_data'])
        elif response['internal_search']:
            search_index = response['function_data']
            page_title = "SpicerHome Search"


            context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_index': search_index,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
                # 'cookie_name': current_app.short_session_cookie_name
            }

            return render_template('internal/search/search_index.html', **context)
    
    else:        
        page_title = "SpicerHome Search"

        print(current_user.json_sidebar_links())

        context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
                # 'cookie_name': current_app.short_session_cookie_name
            }

        return render_template('internal/search/index.html', **context)

@blp.route('/search/query=<user_query>')
@login_required
def redirect_old1_search_command(user_query):
    return redirect(f"/internal/search?q={user_query}")

@blp.route('/search/history')
def history():
    user_sub = current_user.id
    user_history_query = current_user.requests

    user_history_query_structured = {user_sub: {}}
    for history_request in user_history_query:
        if history_request.is_search == True:
            try:
                user_query_url = history_request.command.search_url.format(history_request.encoded_query)
            except AttributeError:
                user_query_url = history_request.command.url
        elif history_request.is_search == False:
            user_query_url = history_request.command.url

        user_history_query_structured[user_sub][history_request.id] = {
            "request_id": history_request.id,
            "original_request": history_request.original_request,
            "query_url": user_query_url,
            "date_and_time": history_request.datetime_of_request
        }
    
    page_title = "SpicerHome History"

    context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links(),
                'history_requests': user_history_query_structured
            }

    return render_template('/internal/search/history.html', **context)


@blp.route('/search/track')
def tracking():
    user_sub = current_user.id

    user_track_query = TrackingNumbersModel.query.filter_by(user_id=user_sub).order_by(TrackingNumbersModel.id.desc()).all()

    user_track_query_structured = {user_sub: {}}
    for track_request in user_track_query:
        tracking = get_tracking_number(track_request.tracking_number)
        user_track_query_structured[user_sub][track_request.id] = {
            "track_id": track_request.id,
            "tracking_number": track_request.tracking_number,
            "query_url": tracking.tracking_url,
            "courier_name": tracking.courier.name,
            "is_active": track_request.is_active,
            "note": track_request.note,
            "datetime_of_create_on_database": track_request.datetime_of_create_on_database
        }


    page_title = "SpicerHome Tracking"

    context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links(),
                'tracking_requests': user_track_query_structured
            }

    return render_template('/internal/search/tracking.html', **context)

@blp.route('/search/commands')
def commands():
    # data = current_app.data
    page_title = "SpicerHome Commands"

    context = {
                'user_default_search_id': current_user.default_search_id,
                'user_theme': current_user.user_theme,
                'search_commands': current_user.json_user_search_commands(),
                'commands': current_user.json_user_commands(),
                'page_title': page_title,
                'sidebar_links': current_user.json_sidebar_links()
            }

    return render_template('/internal/search/commands.html', **context)