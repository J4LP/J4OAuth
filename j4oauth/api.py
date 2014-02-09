from flask import Blueprint, jsonify
from j4oauth.app import oauth

api = Blueprint('api', __name__)


@api.route('/v1/auth_user')
@oauth.require_oauth('info')
def auth_user(req):
    """
    Example of a oauth request, req.user will contain the user model.
    We also protected this request with the scope 'info'
    """
    return jsonify(user={
        'main_character': req.user.character_name,
        'corporation': req.user.main_corporation,
        'alliance': req.user.main_alliance
    })
