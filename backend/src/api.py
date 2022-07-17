# from crypt import methods
import os
# from tkinter import N
# from turtle import title
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS, cross_origin

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

DRINKS_PER_PAGE = 10


def paginate_drinks_short(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * DRINKS_PER_PAGE
    end = start + DRINKS_PER_PAGE
    drinks = [drink.short() for drink in selection]
    current_page = drinks[start:end]
    return current_page

def paginate_drinks_long(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * DRINKS_PER_PAGE
    end = start + DRINKS_PER_PAGE
    drinks = [drink.long() for drink in selection]
    current_page = drinks[start:end]
    return current_page

app = Flask(__name__)
setup_db(app)

"""
setting up CORS Allow '*' for origins. 

"""
cors = CORS(app, resources={r'/*':  {'origins':'*'}})

"""
setting up Access-Control-Allow for headers and methods

"""
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 
    'Content-Type,Authorization,true')

    response.headers.add('Acess-Control-Allow-Methods', 
    'GET,POST,PATCH,DELETE,OPTIONS')

    return response

'''
uncomment the following line to initialize the datbase
HIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES
'''
GET /drinks
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
or appropriate status code indicating reason for failure
'''

@cross_origin
@app.route('/drinks', methods=['GET'])
def retrieve_drinks_short():
    selection = Drink.query.order_by(Drink.id).all()
    current_drinks = paginate_drinks_short(request, selection)

    return jsonify({
        'success': True,
        'drinks': current_drinks,
    }), 200

'''
    GET /drinks-detail
requires the 'get:drinks-detail' permission
returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
or appropriate status code indicating reason for failure
'''
@cross_origin
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def retrieve_drinks_long():
    selection = Drink.query.order_by(Drink.id).all()
    current_drinks = paginate_drinks_long(request, selection)

    return jsonify({
        'success': True,
        'drinks' : current_drinks
    }), 200


'''
POST /drinks
it requires the 'post:drinks' permission
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
or appropriate status code indicating reason for failure

'''
@cross_origin
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_new_drink():
    body = request.get_json()
    if body is None:
        abort(400)

    new_title = body.get('title', None)
    new_recipe = json.dumps(body.get('recipe', None))

    if new_title is None or new_recipe is None:
        abort(422)

    new_drink = Drink(title=new_title, recipe=new_recipe)
    new_drink.insert()

    return jsonify({
        'successs': True,
        'drinks': [new_drink.long()]
    }), 200

'''
PATCH /drinks/<id>    
requires the 'patch:drinks' permission and
contains the drink.long() data representation
returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
or appropriate status code indicating reason for failure
'''
@cross_origin
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
    if drink is None:
        abort(404)

    body = request.get_json()
    if body is None:
        abort(400)
    
    new_title = body.get('title', None)
    new_recipe = json.dumps(body.get('recipe', None))

    if new_title is None and new_recipe is None:
        abort(422)

    if new_title:
        drink.title = new_title

    if new_recipe:
        drink.recipe = new_recipe

    drink.update()

    return jsonify({
        'success': True,
        'drinks': [drink.long()]
    }), 200

    



'''

DELETE /drinks/<id>
where <id> is the existing model id
respond with 404 error if <id> is not found
delete the corresponding row for <id>
requires the 'delete:drinks' permission
returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
or appropriate status code indicating reason for failure
'''
@cross_origin
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if drink is None:
        abort(404)

    drink.delete()

    return jsonify({
        'success': True,
        'delete': drink_id
    }), 200


# Error Handling

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(422)
def Unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
    }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'bad request'
    }), 400

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed'
    }), 405



'''
error handler for AuthError

'''
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code