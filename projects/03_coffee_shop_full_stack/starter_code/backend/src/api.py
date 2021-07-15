import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth
from werkzeug.datastructures import ImmutableMultiDict

app = Flask(__name__)
setup_db(app)
CORS(app)


# To initialize the datbase, I have to uncomment the following line

db_drop_and_create_all()

# ROUTES

# GET /drinks:
# It's a public endpoint that contain only the drink.short() data representation.
# Returns status code 200 and json or the error handler.


@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        return json.dumps({
            'success':
            True,
            'drinks': [drink.short() for drink in Drink.query.all()]
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "An Error Occurred"
        }), 500


# GET /drinks-detail:
# It's a public endpoint that contain all drinks with drink.long() data representation.
# Returns status code 200 and json or the error handler.
@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(f):
    try:
        return json.dumps({
            'success':
            True,
            'drinks': [drink.long() for drink in Drink.query.all()]
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "An Error Occurred"
        }), 500


# POST /drinks:
# It's a public endpoint that create a new row in the drinks table with drink.long() data representation.
# Returns status code 200 and json or the error handler.
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(f):

    data = dict(request.form or request.json or request.data)
    drink = Drink(title=data.get('title'),
                  recipe=data.get('recipe') if type(data.get('recipe')) == str
                  else json.dumps(data.get('recipe')))
    try:
        drink.insert()
        return json.dumps({
            'success': True,
            'drink': drink.long()
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "An Error Occurred"
        }), 500


# PATCH /drinks/<id>:
# Require the patch drinks permission with drink.long() data representation that will update drink if it exists.
# Returns status code 200 and json or the error handler.
@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(f, id):

    try:
        data = dict(request.form or request.json or request.data)
        drink = drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink:
            drink.title = data.get('title') if data.get(
                'title') else drink.title
            recipe = data.get('recipe') if data.get('recipe') else drink.recipe
            drink.recipe = recipe if type(recipe) == str else json.dumps(
                recipe)
            drink.update()
            return json.dumps({'success': True, 'drinks': [drink.long()]}), 200
        else:
            return json.dumps({
                'success':
                False,
                'error':
                'Drink #' + id + ' Not Found To Be Updated'
            }), 404
    except:
        return json.dumps({
            'success': False,
            'error': "An Error Occurred"
        }), 500


# DELETE /drinks/<id>:
# It's require the delete drinks permission. Will delete drinks if it exists.
# Returns status code 200 and json or or the error handler.
@app.route('/drinks/<id>', methods=['DELETE'])
@requires_auth('patch:drinks')
def drinks(f, id):

    try:
        drink = drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink:
            drink.delete()
            return json.dumps({'success': True, 'drink': id}), 200
        else:
            return json.dumps({
                'success':
                False,
                'error':
                'Drink #' + id + ' Not Found To Be Deleted'
            }), 404
    except:
        return json.dumps({
            'success': False,
            'error': "An Error Occurred"
        }), 500


# Error Handling:
# Example error handling for unprocessable entity
@app.errorhandler(422)
def unprocessable(error):

    return jsonify({
        "success": False,
        "error": 422,
        "message": "Unprocessable"
    }), 422


@app.errorhandler(400)
def unprocessable(error):

    return jsonify({
        "success": False,
        "error": 400,
        "message": "Check The Body Request"
    }), 400


@app.errorhandler(404)
def unprocessable(error):

    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource Not Found"
    }), 404


# Error handler for AuthError:
@app.errorhandler(AuthError)
def handle_auth_error(ex):

    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
