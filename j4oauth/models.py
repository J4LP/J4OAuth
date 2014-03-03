# -*- coding: utf-8 -*-
import json
from werkzeug.security import gen_salt
from j4oauth.app import db, ldaptools, redis


class Client(db.Model):
    # human readable name, not required
    name = db.Column(db.String(40))

    # human readable description, not required
    description = db.Column(db.String(400))

    homepage = db.Column(db.String(255))

    # creator of the client, not required
    user_id = db.Column(db.String(255))

    client_id = db.Column(db.String(40), primary_key=True)
    client_secret = db.Column(db.String(55), unique=True, index=True,
                              nullable=False)

    # public or confidential
    is_confidential = db.Column(db.Boolean)

    admin_access = db.Column(db.Boolean, default=False)

    _redirect_uris = db.Column(db.Text)
    _default_scopes = db.Column(db.Text)

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'confidential'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []

    @property
    def user(self):
        return ldaptools.get_user(self.user_id)

    def generate_keys(self):
        self.client_id = gen_salt(40)
        self.client_secret = gen_salt(55)

    def generate_secret(self):
        self.client_secret = gen_salt(55)


class Grant(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.String(255))

    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client')

    code = db.Column(db.String(255), index=True, nullable=False)

    redirect_uri = db.Column(db.String(255))
    expires = db.Column(db.DateTime)

    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def user(self):
        return ldaptools.get_user(self.user_id)


class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.String(40), db.ForeignKey('client.client_id'),
        nullable=False,
    )
    client = db.relationship('Client', backref='tokens')

    user_id = db.Column(db.String(255))

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []

    @property
    def user(self):
        return ldaptools.get_user(self.user_id)


class Scope(db.Model):
    slug = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.Text)
    icon = db.Column(db.String(40))

    @staticmethod
    def from_dict(data):
        """
        Returns a new Scope from a dict
        """
        self = Scope()
        for c in self.__table__.columns:
            if c.name in data:
                setattr(self, c.name, data[c.name])
        return self

    def to_dict(self):
        """
        Return a dict for easy serialization
        """
        return {
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'icon': self.icon
        }

    @staticmethod
    def all():
        """
        Return the list of scopes from cache or build it and cache it
        """
        scopes = redis.get('j4oauth:scopes')
        if scopes is None:
            _scopes = Scope.query.all()
            redis.set('j4oauth:scopes', json.dumps([scope.to_dict()
                                                    for scope in _scopes]))
            redis.expire('j4oauth:scopes', 60 * 60)
            scopes = {scope.slug: scope for scope in _scopes}
        else:
            scopes = {scope['slug']: Scope.from_dict(scope)
                      for scope in json.loads(scopes)}
        return scopes
