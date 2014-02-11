from flask import abort, Blueprint, flash, redirect, render_template, url_for
from flask.ext.login import current_user, login_required
from j4oauth.app import app, db
from j4oauth.forms import ClientForm
from j4oauth.models import Client, Token

account = Blueprint('account', __name__, template_folder='templates/account')


@account.route('')
@login_required
def user_account():
    """
    View for user settings
    """
    tokens = Token.query.filter_by(user_id=current_user.id).all()
    applications = Client.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html',
                           tokens=tokens, applications=applications)


@account.route('/applications/<client_id>', methods=['GET', 'POST'])
@login_required
def application(client_id):
    """
    View for application settings and stats
    """
    client = Client.query.get(client_id)
    client_form = ClientForm(obj=client, redirect_uri=client._redirect_uris)
    if client is None:
        abort(404)
    if client.user_id != current_user.id:
        app.logger.warning('Security issue by {}'.format(current_user.id))
        flash('You are not allowed to do that', 'danger')
        return redirect(url_for('.user_account'))
    if client_form.validate_on_submit():
        client.name = client_form.name.data
        client.description = client_form.description.data
        client.homepage = client_form.homepage.data
        client._redirect_uris = client_form.redirect_uri.data
        db.session.add(client)
        try:
            db.session.commit()
        except Exception as e:
            app.logger.exception(e)
            flash('There was an issue updating your application, '
                  'please try again or contact support', 'danger')
        else:
            flash('Application updated', 'success')
        return redirect(url_for('.application', client_id=client.client_id))
    if client_form.is_submitted() is True:
        flash('There was an issue validating your informations', 'danger')
    return render_template('application.html', client=client, form=client_form)


@account.route('/applications/<client_id>/revoke_tokens', methods=['POST'])
@login_required
def application_revoke_tokens(client_id):
    client = Client.query.get(client_id)
    if client is None:
        abort(404)
    if client.user_id != current_user.id:
        app.logger.warning('Security issue by {}'.format(current_user.id))
        flash('You are not allowed to do that', 'danger')
        return redirect(url_for('.user_account'))
    if len(client.tokens) > 1:
        db.session.delete(client.tokens)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        flash('There was an issue revoking this application\'s tokens, '
              'please try again or contact support', 'danger')
    else:
        flash('Tokens revoked with success', 'success')
    return redirect(url_for('.application', client_id=client.client_id))


@account.route('/applications/<client_id>/refresh_secret', methods=['POST'])
@login_required
def application_refresh_secret(client_id):
    client = Client.query.get(client_id)
    if client is None:
        abort(404)
    if client.user_id != current_user.id:
        app.logger.warning('Security issue by {}'.format(current_user.id))
        flash('You are not allowed to do that', 'danger')
        return redirect(url_for('.user_account'))
    client.generate_secret()
    db.session.add(client)
    try:
        db.session.commit()
    except Exception as e:
        app.logger.exception(e)
        flash('There was an issue refreshing this application\'s secret, '
              'please try again or contact support', 'danger')
    else:
        flash('Client secret refreshed', 'success')
    return redirect(url_for('.application', client_id=client.client_id))


@account.route('/revoke/<int:token_id>')
@login_required
def revoke_token(token_id):
    """
    Method to remove a user's token
    :param token_id: the token primary id
    """
    token = Token.query.get(token_id)
    if token is not None:
        try:
            db.session.delete(token)
            db.session.commit()
        except Exception as e:
            app.logger.exception(e)
            flash(
                'There was an issue revoking this application, please try '
                'again or contact support', 'danger')
    else:
        flash('Authorization not found, please try again or contact support',
              'danger')
    return redirect(url_for('.user_account'))


@account.route('/new_application', methods=['GET', 'POST'])
@login_required
def new_application():
    """
    Method to create a new client associated to the current user account
    """
    if 'inpatients' not in current_user.groups:
        app.logger.warning('Security issue by {}'.format(current_user.id))
        flash('You do not belong to the right group for this', 'danger')
        return redirect(url_for('.user_account'))
    client_form = ClientForm()
    if client_form.validate_on_submit():
        client = Client()
        client.name = client_form.name.data
        client.description = client_form.description.data
        client.homepage = client_form.homepage.data
        client._redirect_uris = client_form.redirect_uri.data
        client.generate_keys()
        client.user_id = current_user.id
        client.is_confidential = True
        client._default_scopes = 'auth_info'
        db.session.add(client)
        try:
            db.session.commit()
        except Exception as e:
            app.logger.exception(e)
            flash('There was an issue saving your new application, '
                  'please try again or contact support', 'danger')
        else:
            flash('Application created', 'success')
            return redirect(url_for('.user_account'))
        return redirect(url_for('.new_application'))
    if client_form.is_submitted() is True:
        flash('There was an issue validating your demand', 'danger')
    return render_template('new_application.html', form=client_form)
