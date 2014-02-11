from flask import Blueprint, jsonify
from j4oauth.app import oauth
from j4oauth.evetools import EveTools

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
