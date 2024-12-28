from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from tracking_numbers import get_tracking_number
from flask import session, current_app, url_for
from flask_login import current_user
import urllib.parse
import logging
import requests

from models import db, TrackingNumbersModel, RequestsModel, CommandsModel

def tracking_number(search_query_prefix):

    tracking_details = get_tracking_number(search_query_prefix.upper())
    # print(f"Tracking.py data - {data}")
    if tracking_details == None:
        return None

    # => TrackingNumber(
    #       valid=False,
    #       number='1ZY0X1930320121606',
    #       serial_number=[6, 0, 5, 1, 9, 3, 0, 3, 2, 0, 1, 2, 1, 6, 0],
    #       tracking_url='https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums=1ZY0X1930320121604',
    #       courier=Courier(code='ups', name='UPS'),
    #       product=Product(name='UPS'),
    #    )

    track_query = TrackingNumbersModel.query.filter_by(tracking_number=tracking_details.number,user_id=current_user.id).first()
    if track_query:
        print({"message": "Track request previously recorded."})
        return url_for('internal.tracking')

    else:

        request_dict = {
            "user_id": current_user.id,
            "tracking_number": search_query_prefix.upper(),
            "datetime_of_create_on_database": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                }

        print("track_request data = ", request_dict)

        request_model = TrackingNumbersModel(**request_dict)

        try:
            db.session.add(request_model)
            db.session.commit()
            print("Track request recorded.")
            return url_for('internal.tracking')
        except SQLAlchemyError as e:
            print(e)
            print("Failed to record search request.")
            return url_for('internal.tracking')
        
def shortcuts(user_query):

    search_query_prefix = user_query.split(' ')[0].lower()
    search_query_suffix = user_query.replace(search_query_prefix, '', 1).strip()

    is_search = bool(search_query_suffix)

    user_commands = current_user.json_user_commands()
    shortcut_command = next((cmd for cmd in user_commands if cmd['prefix'] == search_query_prefix), None)

    if not shortcut_command:
        logging.info(f"User search '{user_query}' was not a shortcut.")
        return None

    encoded_query = urllib.parse.quote_plus(search_query_suffix) if is_search and shortcut_command.get('search_url') else None

    if is_search and not encoded_query:
        logging.info(f"User search '{user_query}' shortcut does not have 'search_url'.")
        return None

    request_dict_format = {
        "original_request": user_query,
        "user_id": current_user.id,
        "prefix": search_query_prefix,
        "search_query": search_query_suffix,
        "encoded_query": encoded_query,
        "is_search": is_search,
        "command_id": shortcut_command['id'],
        "datetime_of_request": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    }

    request_model = RequestsModel(**request_dict_format)

    try:
        db.session.add(request_model)
        db.session.commit()
        print("Search request recorded.")
    except SQLAlchemyError as e:
        print(e)
        print("Failed to record search request.")

    function_return = shortcut_command['search_url'].format(encoded_query) if is_search else shortcut_command['url']
    logging.info(f"Shortcuts return - '{function_return}'.")

    return function_return

def search(user_query, user_offset, user_source):
    # original_request = data[2]
    user_query_prefix = user_query.split(' ')[0].lower()
    # print(user_query)

    search_query = user_query.replace(user_query_prefix, '', 1).strip()
    if search_query == "":
        search_query = None
        is_search = False

    search_query = user_query
    # user_query_original_request = user_query
    encoded_search_query = urllib.parse.quote_plus(search_query)
    is_search = True

    user_command_model = CommandsModel.query.filter_by(id=current_user.default_search_id).first()
    user_command = user_command_model.to_dict()

    request_dict_format = {
        "original_request": user_query,
        "user_id": current_user.id,
        "prefix": user_query_prefix,
        "search_query": search_query,
        "encoded_query": encoded_search_query,
        "is_search": is_search,
        "command_id": user_command.get('id', "Error"),
        "datetime_of_request": datetime.now(timezone.utc)
        # "datetime_of_request": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            }

    # print("search_request data = ", request_dict_format)

    request_model = RequestsModel(**request_dict_format)

    try:
        db.session.add(request_model)
        db.session.commit()
        print("Search request recorded.")
    except SQLAlchemyError as e:
        print(e)
        print("Failed to record search request.")
    
    # if user_command['url'] != "/internal/search":
    #     return {"funtion_triggered": True, "funtion_return": user_command['search_url'].format(user_query['encoded_query'])}
    
    if user_command['category'] == "default_search":
        # for permission in data['user_permissions']:
        #     if permission['permission_name'] == "commands" and permission['permission_level'] <= 50:
        base_url = "https://api.search.brave.com/res/v1/"
        endpoint = "web"
        url = base_url + endpoint + "/search"
        headers = {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": current_app.BRAVE_API_KEY}

        params = {"q": user_query,"country": "US","search_lang": "en","ui_lang": "en-US","count": 20,"offset": user_offset,"safesearch": "strict","freshness": None,"text_decorations": None,"result_filter": "web,videos","goggles_id": None,"units": None,"extra_snippets": None}
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(url, headers=headers, params=params)
        search_results = response.json()
        # with open('search_results.txt', 'w') as file:
        #     file.write(json.dumps(search_results, indent=4))


        # search_results = Brave().search(q=user_query, count=20, offset=user_offset)
        # print(search_results)
        return True, search_results

    else:
        return False, user_command['search_url'].format(encoded_search_query)
        # pass