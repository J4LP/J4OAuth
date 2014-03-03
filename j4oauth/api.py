from flask import Blueprint, jsonify
from j4oauth.app import ldaptools, oauth
from j4oauth.evetools import EveTools
from j4oauth.utils import api_check

api = Blueprint('api', __name__)


@api.route('/v1/auth_user')
@oauth.require_oauth('auth_info')
def auth_user(req):
    """
    Example of a oauth request, req.user will contain the user model.
    We also protected this request with the scope 'info'
    """
    return jsonify(user={
        'main_character': req.user.character_name,
        'corporation': req.user.main_corporation,
        'alliance': req.user.main_alliance,
        'auth_status': req.user.accountStatus[0]
    })


@api.route('/v1/auth_groups')
@oauth.require_oauth('auth_groups')
def auth_groups(req):
    """
    Return Auth groups
    """
    return jsonify(groups=[group for group in req.user.get_authgroups()])

@api.route('/v1/characters')
@oauth.require_oauth('characters')
def characters(req):
    """
    This will return every character associated with the Auth API Key as well
    as their limited data
    """
    eve = EveTools(key_id=req.user.keyID[0], vcode=req.user.vCode[0])
    return jsonify(
        characters=[EveTools.element_to_dict(character)
                    for character in eve.get_characters()])



@api.route('/v1/corporation/<corporation_name>/users')
@api_check
def corporation_users(resp, corporation_name):
    """
    Returns all the corporation users
    """
    if not resp.client.admin_access:
        return jsonify(error='Unauthorized access'), 403
    users = ldaptools.get_users('corporation={}'.format(corporation_name))
    return jsonify(users=[{
        'user_id': user.id,
        'character': user.character_name,
        'corporation': user.main_corporation,
        'alliance': user.main_alliance,
        'status': user.status
    } for user in users])


@api.route('/v1/user/<username>')
@api_check
def user_info(username):
    """
    Returns all the auth info for a specific user
    """
    user = ldaptools.get_user(username)
    return jsonify(user={
        'main_character': user.character_name,
        'corporation': user.main_corporation,
        'alliance': user.main_alliance,
        'auth_status': user.accountStatus[0]
    })


@api.route('/v1/user/<username>/skills')
@api_check
def user_skills(username):
    """
    Returns all the skills for a specific user
    """
    user = ldaptools.get_user(username)
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    return jsonify(skills=eve.get_skills(user.character_id))


@api.route('/v1/user/<username>/assets')
@api_check
def user_assets(username):
    """
    Returns all the assets for a specific user
    """
    return jsonify(assets=[])
