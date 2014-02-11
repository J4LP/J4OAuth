# -*- coding: utf-8 -*-
import os
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask.ext.assets import Environment
from flask.ext.login import LoginManager
from flask.ext.migrate import Migrate
from flask.ext.sqlalchemy import SQLAlchemy
from flask_redis import Redis
from flask_wtf.csrf import CsrfProtect
from flask_oauthlib.provider import OAuth2Provider
from webassets.loaders import PythonLoader
from j4oauth import assets
from j4oauth.utils import ReverseProxied

app = Flask(__name__)

app.wsgi_app = ReverseProxied(app.wsgi_app)

# The environment variable, either 'prod' or 'dev'
env = os.environ.get('J4OAUTH_ENV', 'dev')

# Use the appropriate environment-specific settings
app.config.from_object(
    'j4oauth.settings.{env}Config'.format(env=env.capitalize()))

app.config['ENV'] = env

# Set up logging
file_handler = RotatingFileHandler(app.config['LOG_FILE'])
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(file_handler)

if 'SENTRY_DSN' in app.config:
    from raven.contrib.flask import Sentry
    sentry = Sentry(app)

CsrfProtect(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

from j4oauth.ldaptools import LDAPTools
ldaptools = LDAPTools(app.config)

migrate = Migrate(app, db)

oauth = OAuth2Provider(app)

redis = Redis(app)

# Register asset bundles
assets_env = Environment()
assets_env.init_app(app)
assets_loader = PythonLoader(assets)
for name, bundle in assets_loader.load_bundles().iteritems():
    assets_env.register(name, bundle)
