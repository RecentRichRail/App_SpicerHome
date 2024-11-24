import urllib.parse
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import requests

from models import User, CommandsModel, RequestsModel, db

# Testing
# import json

# data = [current_user, search_query_prefix, search_query, offset]

def run(data):

    # original_request = data[2]
    user_query = data[2]
    user_query_prefix = data[1]
    user_offset = data[3]
    current_user = data[0]
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
        return {"function_triggered": True, "internal_search": True, "function_return": search_results}

    else:
        return {"function_triggered": True, "function_return": user_command['search_url'].format(encoded_search_query)}
        # pass