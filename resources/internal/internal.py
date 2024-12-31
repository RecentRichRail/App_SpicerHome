from flask import Blueprint, render_template, redirect, request, session
from flask_login import login_required, current_user
import logging
from tracking_numbers import get_tracking_number
from models import TrackingNumbersModel

from resources.utils import functions

internal_blueprint = Blueprint("internal", __name__, template_folder="templates")

# import urllib.parse
# from brave import Brave

blp = internal_blueprint

def user_search_query(offset, search_query):
    pass


@blp.route('/search')
@login_required
def internal_search():
    # if request.args.get('query'):
    #     user_query = request.args.get('query')
    user_query = request.args.get('q')
    query_source = request.args.get('source')
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

        search_query_prefix = user_query.split(' ')[0].lower()

        # response = user_search_query(offset, user_query)

        # Would be best to make a admin UI to arrange the order of the functions
        internal_search = False
        tracking_function = functions.tracking_number(search_query_prefix)
        shortcuts_function = functions.shortcuts(user_query)
        if not tracking_function and not shortcuts_function:
            internal_search, search_function = functions.search(user_query, offset, query_source)

        try:
            if not internal_search:
                if tracking_function:
                    logging.debug(f"Tracking function = {tracking_function}")
                    return redirect(tracking_function)
                elif shortcuts_function:
                    logging.debug(f"Shortcuts function = {shortcuts_function}")
                    return redirect(shortcuts_function)
                elif search_function:
                    logging.debug(f"Search function = {search_function}")
                    return redirect(search_function)
            else:
                search_index = search_function
                page_title = "SpicerHome Search"

        except KeyError as e:
            logging.error(f"KeyError = {e}")

        # if not response['internal_search']:
        #     return redirect(response['function_data'])
        # elif response['internal_search']:
        #     search_index = response['function_data']
        page_title = "SpicerHome Search"


        context = {
            'search_index': search_index,
            'page_title': page_title
        }

        session['user_default_search_id'] = current_user.default_search_id
        session['user_theme'] = current_user.user_theme

        return render_template('internal/search/partials/searchbase.html', **context)
    
    else:        
        page_title = "SpicerHome Search"

        # print(current_user.json_sidebar_links())

        context = {
                'page_title': page_title
            }

        return render_template('internal/index.html', **context)

@blp.route('/search/query=<user_query>')
@login_required
def redirect_old1_search_command(user_query):
    return redirect(f"/internal/search?q={user_query}")

@blp.route('/settings')
@login_required
def user_settings():
    page_title = "SpicerHome Settings"

    context = {
                'page_title': page_title
            }

    return render_template('/internal/user_profile/settingsbase.html', **context)

@blp.route('/search/history')
def history():
    user_sub = current_user.id
    user_history_query = current_user.requests

    user_history_query_structured = {current_user.id: {}}
    for history_request in user_history_query[::-1]:
        if history_request.is_search == True:
            try:
                user_query_url = history_request.command.search_url.format(history_request.encoded_query)
            except AttributeError:
                user_query_url = history_request.command.url
        elif history_request.is_search == False:
            user_query_url = history_request.command.url

        user_history_query_structured[current_user.id][history_request.id] = {
            "request_id": history_request.id,
            "original_request": history_request.original_request,
            "query_url": user_query_url,
            "date_and_time": history_request.datetime_of_request
        }
    
    page_title = "SpicerHome History"

    context = {
                'page_title': page_title,
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
                'page_title': page_title,
                'tracking_requests': user_track_query_structured
            }

    return render_template('/internal/search/tracking.html', **context)

@blp.route('/search/commands')
def commands():
    # data = current_app.data
    page_title = "SpicerHome Commands"

    context = {
                'page_title': page_title
            }

    return render_template('/internal/search/commands.html', **context)