import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import json


AUTH0_DOMAIN = 'dev-06u0yfz9.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'http://127.0.0.1:5000'

# AuthError Exception

# AuthError Exception
# A standardized way to communicate auth failure modes


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

# get_token_auth_header() method:
# Get the access token from the Authorization Header.
def get_token_auth_header():
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization Header is Expected"
            }, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization Header Must Start With"
                " Bearer"
            }, 401)
    elif len(parts) == 1:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Token Not Found"
            }, 401)
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization Header Must Be"
                " Bearer token"
            }, 401)

    token = parts[1]
    return token


# check_permissions(permission, payload) method:
# Checks if the decoded JWT has the required permission.
def check_permissions(permission, payload):
    if payload.get('permissions'):
        token_scopes = payload.get("permissions")
        if (permission not in token_scopes):
            raise AuthError(
                {
                    'code': 'invalid_permissions',
                    'description': 'User Does Not Have Enough Privileges'
                }, 401)
        else:
            return True
    else:
        raise AuthError(
            {
                'code': 'invalid_permissions',
                'description': 'User Does Not Have Any Roles Attached'
            }, 401)


# verify_decode_jwt(token) method:
# Receives the encoded token and validates it after decoded.
# Note urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'Authorization Malformed.'
            }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(token, rsa_key, algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer='https://' + AUTH0_DOMAIN + '/')

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError(
                {
                    'code': 'token_expired',
                    'description': 'Token Expired.'
                }, 401)

        except jwt.JWTClaimsError:
            raise AuthError(
                {
                    'code':
                    'invalid_claims',
                    'description': 'Incorrect Claims. Please, Check the Audience and Issuer.'
                }, 401)
        except Exception:
            raise AuthError(
                {
                    'code': 'invalid_header',
                    'description': 'Unable to Parse Authentication Token.'
                }, 400)
    raise AuthError(
        {
            'code': 'invalid_header',
            'description': 'Unable to Find the Appropriate Key.'
        }, 400)


# requires_auth(permission) decorator method:
# use get_token_auth_header method to get the token.
# use verify_decode_jwt method to decode the jwt.
# use  check_permissions method validate claims and check the requested permission.
# return the decorator which passes the decoded payload to the decorated method.
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()

            try:
                payload = verify_decode_jwt(token)
            except:
                raise AuthError({
                    'code': 'invalid token',
                    'description': 'Invalid Token'
                }, 401)

            check_permissions(permission, payload)

            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator
