# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from flask import flash, redirect, render_template, request, session, url_for
from flask.ext.login import current_user, login_required, login_user, \
    logout_user
from jinja2 import Markup
from j4oauth.account import account
from j4oauth.api import api
from j4oauth.app import app, db, ldaptools, login_manager, oauth
from j4oauth.forms import LoginForm
from j4oauth.models import Client, Token, Grant, Scope

login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    return ldaptools.get_user(userid)


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login view, ties with our LDAP authentication and Flask-Login
    """
    if current_user.is_authenticated():
        # Probably coming from an OAuth request
        return redirect(request.args.get('next') or url_for('home'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        try:
            ldap_check = ldaptools.check_credentials(
                login_form.username.data, login_form.password.data)
        except Exception as e:
            # Check credentials raise an exception if there's a server issue
            flash(
                'Due to a server issue, we could not authenticate you. '
                'Please wait a bit and try again', 'danger')
            return redirect(url_for('login'))
        if ldap_check:
            user = ldaptools.get_user(login_form.username.data)
            session['admin'] = False
            if 'admin' in user.get_authgroups():
                session['admin'] = True
            login_user(user)
            app.logger.info(
                'User {0} successfully logged into J4OAUTH'.format(
                    user.get_id()))
            if request.form.get('next') == 'None':
                return redirect(url_for('home'))
            else:
                return redirect(request.form.get('next'))
        else:
            # Bad nerd
            flash('Invalid credentials, please try again.', 'danger')
            if request.form.get('next') == 'None':
                return redirect(url_for('login'))
            else:
                return redirect(url_for('login') + request.form.get('next'))
    if login_form.is_submitted() is True:
        # Form was submitted but invalid
        flash('There was an error logging you in, '
              'please check your credentials', 'danger')
    return render_template('login.html',
                           form=login_form, next=request.args.get('next'))


@app.route('/logout', methods=['GET'])
def logout():
    """
    Logout view
    """
    logout_user()
    session.clear()
    return redirect(url_for('home'))


@app.route('/authorize', methods=['GET', 'POST'])
@oauth.authorize_handler
@login_required
def authorize(*args, **kwargs):
    """
    OAuth authorization screen, will display the list of scopes and a yes/no
    TODO: Make sure this is somewhat secure
    """
    client_id = kwargs.get('client_id')
    client = Client.query.filter_by(client_id=client_id).first()
    kwargs['client'] = client
    if request.method == 'GET':
        # Let's see if we don't already have a token for this user/app ?
        token = Token.query.filter_by(
            user_id=current_user.id, client_id=client_id).first()
        kwargs['Scopes'] = Scope.all()
        if token and token.scopes != kwargs['scopes']:
            # We already have a token but different permissions
            kwargs['token'] = token
            kwargs['new_scopes'] = [scope for scope in kwargs['scopes']
                                    if scope not in token.scopes]
            return render_template('oauth_authorize_scopes.html',
                                   query_string=request.query_string, **kwargs)
        if not token:
            # No ? Let's ask the user then
            return render_template('oauth_authorize.html',
                                   query_string=request.query_string, **kwargs)
        # Everything match ? Done.
        return oauth.confirm_authorization_request()
    # Request is POST
    return request.form.get('accept', 'false') == 'true'


@app.route('/token', methods=['GET'])
@oauth.token_handler
def access_token():
    return None


@app.route('/errors')
def oauth_errors():
    return render_template('oauth_error.html', error=request.args.get('error'))


@oauth.clientgetter
def load_client(client_id):
    return Client.query.filter_by(client_id=client_id).first()


@oauth.grantgetter
def load_grant(client_id, code):
    return Grant.query.filter_by(client_id=client_id, code=code).first()


@oauth.grantsetter
def save_grant(client_id, code, request, *args, **kwargs):
    # TODO: Grants are temporary, should put them in redis or somewhere
    expires = datetime.utcnow() + timedelta(seconds=100)
    grant = Grant(
        client_id=client_id,
        code=code['code'],
        redirect_uri=request.redirect_uri,
        _scopes=' '.join(request.scopes),
        user_id=current_user.get_id(),
        expires=expires
    )
    db.session.add(grant)
    db.session.commit()
    return grant


@oauth.tokengetter
def load_token(access_token=None, refresh_token=None):
    if access_token:
        return Token.query.filter_by(access_token=access_token).first()
    elif refresh_token:
        return Token.query.filter_by(refresh_token=refresh_token).first()


@oauth.tokensetter
def save_token(token, request, *args, **kwargs):
    tokens = Token.query.filter_by(client_id=request.client.client_id,
                                   user_id=request.user.id)
    # make sure that every client has only one token connected to a user
    for t in tokens:
        db.session.delete(t)

    expires_in = token.pop('expires_in')
    expires = datetime.utcnow() + timedelta(seconds=expires_in)

    token = Token(
        access_token=token['access_token'],
        refresh_token=token['refresh_token'],
        token_type=token['token_type'],
        _scopes=token['scope'],
        expires=expires,
        client_id=request.client.client_id,
        user_id=request.user.id,
    )
    db.session.add(token)
    db.session.commit()
    return token


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@app.context_processor
def inject_icon():
    """
    Handy template method for quick icons
    """
    def icon(icon_name):
        return Markup('<i class="fa fa-{icon}"></i>'.format(icon=icon_name))
    return dict(icon=icon)


@app.context_processor
def inject_globals():
    return dict(
        APPLICATION_ROOT=app.config['APPLICATION_ROOT']
    )

app.register_blueprint(account, url_prefix='/account')
app.register_blueprint(api, url_prefix='/api')
