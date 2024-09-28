from flask import current_app
import requests

#  data = [current_user, search_query_prefix, search_query, offset]

def run(data):
    if current_app.server_env == "prod":
        for permission in data[0].permissions:
            if permission.permission_name == "dev" and permission.permission_level <= 999:
                response = requests.get(f"{current_app.dev_server}/external/status")
                # dev_server_status = response.json()

                if response.status_code == 200:
                    dev_user_query = data[2]
                    return {"funtion_triggered": True, "funtion_return": f"{current_app.dev_server}/internal/search?q={dev_user_query}"}
                
                else:
                    return {"function_triggered": False}
            
    return {"function_triggered": False}