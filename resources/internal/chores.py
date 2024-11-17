from flask import Blueprint, request, jsonify, current_app, render_template
import os
import requests
from models import ChoresUser
from models import db

chores_blueprint = Blueprint("chores", __name__, template_folder="templates")

@chores_blueprint.route('/points', methods=['POST'])
def chores_test():
    print('1a - Here')
    data = request.get_json()
    name = data.get('name')
    # print(f'1b - {name}')
    action = data.get('action')
    print(f'1c - {action}')
    points = data.get('points')
    # print(f'1d - {points}')

    if not action or (action != 'get' and (not name or points is None)):
        print(f'2a - Here')
        return {"message": "Invalid input"}, 400

    if action == 'get':
        if not name:
            users = ChoresUser.query.all()
            all_users_points = {user.name: user.points for user in users}
            return {"message": "success", "points": all_users_points}, 200
        user = ChoresUser.query.filter_by(name=name).first()
        if not user:
            return {"message": "User not found"}, 404
        return {"message": "success", "points": user.points}, 200

    user = ChoresUser.query.filter_by(name=name).first()
    if not user:
        user = ChoresUser(name=name, points=0)
        db.session.add(user)

    if action == 'add':
        user.points += points
    elif action == 'subtract':
        user.points -= points
    else:
        print(f'1b - {action}')
        return {"message": "Invalid action"}, 400

    db.session.commit()
    return {"message": "success", "points": user.points}, 200