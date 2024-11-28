from flask import Blueprint, request, jsonify, current_app
import os
import requests
from models import User, CommandsModel, BananaGameUserBananasModel, BananaGameLifetimeBananasModel, BananaGameButtonPressModel, RequestsModel, TrackingNumbersModel, PermissionsModel
from models import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tracking_numbers import get_tracking_number
from flask_login import login_required, current_user, logout_user
import importlib

def run_funtion(script_path, data):
    spec = importlib.util.spec_from_file_location("module.name", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run(data)

# Thinking on having "Functions" - When a query is sent from the search it loops through funtions
# This will also allow a future UI editor - Create a funtion, the function gets added to codebase, funtion runs
# The actual search will need to be a funtion rather than the logic being done on the front-end
# When a function is not able to preform or is not going to be used will need to have an output the code will understand to go to the next function
# When the function is executed, It will only return a redirect link, that will be sent to the front end and will redirect the user
# @api_blueprint.route("/search/query", methods=['POST'])
@login_required
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
            return jsonify({"internal_search": script_return.get("internal_search", False), "function_data": script_return['funtion_return']})
    except Exception as e:
                print(f"Error running search.py: {e}")
                return {"error": str(e)}
    # print({"redirect_url": run_funtion(os.path.join('resources/functions', 'search.py'), data)['funtion_return']})
    return jsonify({"internal_search": script_return.get("internal_search", False), "function_data": run_funtion(os.path.join('resources/utils/functions', 'search.py'), data)['funtion_return']})