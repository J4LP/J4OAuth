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
        'user_id': req.user.id,
        'main_character': req.user.character_name,
        'main_character_id': req.user.character_id,
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
def corporation_users(corporation_name):
    """
    Returns all the corporation users
    """
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
    Returns all the auth info for a specific user and all its characters
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0])
    characters = eve.safe_request('account/APIKeyInfo').key.characters
    return jsonify(user={
        'user_id': user.id,
        'main_character': user.character_name,
        'corporation': user.main_corporation,
        'alliance': user.main_alliance,
        'auth_status': user.accountStatus[0],
        'auth_groups': [group for group in user.get_authgroups()],
        'characters': [
            {'character_id': character['characterID'],
             'character_name': character['characterName'],
             'corporation_id': character['corporationID'],
             'corporation_name': character['corporationName']}
            for character in characters]
    })


@api.route('/v1/user/<username>/<character_id>/sheet')
@api_check
def user_sheet(username, character_id):
    """
    Return the character sheet for a specific user and character
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    sheet = eve.safe_request('eve/CharacterInfo', {'characterID': character_id})
    return jsonify(sheet=EveTools.auto_to_dict(sheet))


@api.route('/v1/user/<username>/<character_id>/skills')
@api_check
def user_skills(username, character_id):
    """
    Returns all the skills for a specific user
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    return jsonify(skills=eve.get_skills(character_id))


@api.route('/v1/user/<username>/<character_id>/assets')
@api_check
def user_assets(username, character_id):
    """
    Returns all the assets for a specific user and character
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    assets = eve.safe_request('char/AssetList', {'characterID': character_id}).assets
    return jsonify(assets=EveTools.auto_to_dict(assets))


@api.route('/v1/user/<username>/<character_id>/contacts')
@api_check
def user_contacts(username, character_id):
    """
    Returns all the contacts for a specific user and character
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    contacts = eve.safe_request('char/ContactList',
                                {'characterID': character_id}).contactList
    return jsonify(contacts=EveTools.auto_to_dict(contacts))


@api.route('/v1/user/<username>/<character_id>/standings')
@api_check
def user_standings(username, character_id):
    """
    Returns all the standings for a specific user and character
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    standings = eve.safe_request('char/Standings',
                                 {'characterID': character_id}).characterNPCStandings
    return jsonify(standings=EveTools.auto_to_dict(standings))


@api.route('/v1/user/<username>/<character_id>/wallet')
@api_check
def user_wallet(username, character_id):
    """
    Returns the wallet for a specific user and character
    """
    user = ldaptools.get_user(username)
    if user is None:
        return jsonify(), 404
    eve = EveTools(key_id=user.keyID[0], vcode=user.vCode[0], cache=True)
    wallet = eve.safe_request('char/WalletJournal',
                                 {'characterID': character_id}).transactions
    return jsonify(wallet=EveTools.auto_to_dict(wallet))
