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

db_drop_and_create_all()

# ROUTES

@app.route('/drinks', methods=['GET'])
def get_drinks():
    try:
        drinksShortList = [drink.short() for drink in Drink.query.all()]
        return json.dumps({
            'success': True,
            'drinks': drinksShortList
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "Error with loading drinks occured"
        }), 500


@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(f):
    try:
        drinksLongList = [drink.long() for drink in Drink.query.all()]

        return json.dumps({
            'success': True,
            'drinks': drinksLongList
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "Error with loading drinks detail occured"
        }), 500


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drink(f):

    reqData = dict(request.form or request.json or request.data)
    drink = Drink(title=reqData.get('title'), recipe=reqData.get('recipe')
                  if type(reqData.get('recipe')) == str
                  else json.dumps(reqData.get('recipe')))
    try:
        drink.insert()
        return json.dumps({
            'success': True,
            'drink': drink.long()
        }), 200
    except:
        return json.dumps({
            'success': False,
            'error': "Error with adding a drink occured"
        }), 500


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(f, id):

    try:
        reqData = dict(request.form or request.json or request.data)

        drink = drink = Drink.query.filter(Drink.id == id).one_or_none()

        if drink:
            drink.title = reqData.get('title') if reqData.get(
                'title') else drink.title
            drinkRecipe = reqData.get('recipe') if reqData.get(
                'recipe') else drink.recipe
            drink.recipe = drinkRecipe if type(drinkRecipe) == str else json.dumps(
                drinkRecipe)
            drink.update()

            return json.dumps({
                'success': True,
                'drinks': [drink.long()]
            }), 200
        else:
            return json.dumps({
                'success': False,
                'error': 'The drink not found. Update unsuccessful.'
            }), 404
    except:
        return json.dumps({
            'success': False,
            'error': "Error with editing the drink occured"
        }), 500


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
                'success': False,
                'error': 'The drink not found. Deleting unsuccessful.'
            }), 404
    except:
        return json.dumps({
            'success': False,
            'error': "Error with deleting the drink occured"
        }), 500


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
        "message": "Check the body request"
    }), 400


@app.errorhandler(404)
def unprocessable(error):

    return jsonify({
        "success": False,
        "error": 404,
        "message": "Resource not found"
    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(ex):

    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response
