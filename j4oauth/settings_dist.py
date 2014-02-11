# -*- coding: utf-8 -*-
import os

class Config(object):
    SECRET_KEY = 'akV5JQZyKxcwdOTs2ZSK+PeM/r2fOzwguKKfadWJg/4='
    APP_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    LOG_FILE = 'j4oauth.log'
    AUTH = {
        "domain": "j4lp.com",
        "alliance": "I Whip My Slaves Back and Forth",
        "allianceshort": "J4LP"
    }


class ProdConfig(Config):
    CACHE_TYPE = 'simple'
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://j4oauth:j4oauth@db.local/j4oauth' # DB URL
    REDIS = '127.0.0.1'
    LDAP = {
        "server": "ldap:///ldap.local/",
        "admin": "cn=secret,dc=j4lp,dc=com",
        "password": "--secret--",
        "basedn": "dc=j4lp,dc=com",
        "memberdn": "ou=People,dc=j4lp,dc=com"
    }
    APPLICATION_ROOT = '/oauth/'
    REDIS_URL = "redis://:password@localhost:6379/0"


class DevConfig(Config):
    CACHE_TYPE = 'simple'
    DEBUG = True
    DB_NAME = 'j4oauth.db'
    DB_PATH = os.path.join(Config.PROJECT_ROOT, DB_NAME)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{0}'.format(DB_PATH)
    SQLALCHEMY_ECHO = True
    REDIS = '127.0.0.1'
    LDAP = {
        "server": "ldap:///127.0.0.1/",
        "admin": "cn=admin,dc=j4dev,dc=local",
        "password": "admin",
        "basedn": "dc=j4dev,dc=local",
        "memberdn": "ou=People,dc=j4dev,dc=local"
    }
    REDIS_URL = "redis://:password@localhost:6379/0"

