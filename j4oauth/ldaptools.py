#!/usr/bin/env python
import ldap
from flask.ext.login import UserMixin
from j4oauth.app import app


class ServerDownException(Exception):
    pass


class UserPurgedException(Exception):
    pass


class LDAPTools():

    def __init__(self, config):
        self.authconfig = config
        self.config = config['LDAP']

    def get_user(self, id):
        if not isinstance(id, basestring):
            id = id[0]
        l = ldap.initialize(self.config["server"])
        l.simple_bind(self.config["admin"], self.config["password"])
        ldap_filter = "uid=" + id
        result_id = l.search(
            self.config["memberdn"], ldap.SCOPE_SUBTREE, ldap_filter, None)
        if result_id:
            type, data = l.result(result_id, 0)
        if data:
            dn, attrs = data[0]
            l.unbind_s()
            return self.User(attrs, self.authconfig["AUTH"]["domain"])
        l.unbind_s()
        return None

    def check_credentials(self, username, password):
        try:
            ldap_client = ldap.initialize(self.config["server"])
            ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            ldap_client.simple_bind_s(
                "uid=%s,%s" % (username, self.config["memberdn"]), password)
        except (ldap.INVALID_DN_SYNTAX,
                ldap.UNWILLING_TO_PERFORM,
                ldap.SERVER_DOWN) as e:
            app.logger.exception(e)
            ldap_client.unbind()
            return False
        except ldap.INVALID_CREDENTIALS as e:
            app.logger.error('Invalid login attempt for {}'.format(username))
            ldap_client.unbind()
            return False
        ldap_client.unbind()
        if self.is_purged(username):
            return False
        return True

    def is_purged(self, username):
        user = self.get_user(username)
        if user is None:
            return False
        return user.accountStatus[0] == 'purged'

    class User(UserMixin):

        def __init__(self, attr, domain):
            self.__dict__.update(attr)
            self.domain = domain

        def get_id(self):
            return self.uid[0]

        @property
        def character_id(self):
            from j4oauth.evetools import get_character_id  # Circular imports !
            return get_character_id(self.characterName[0])

        @property
        def id(self):
            return self.uid[0]

        @property
        def character_name(self):
            return self.characterName[0]

        @property
        def groups(self):
            return self.get_authgroups()

        @property
        def main_corporation(self):
            return self.corporation[0]

        @property
        def main_alliance(self):
            return self.alliance[0]

        def get_authgroups(self):
            if not hasattr(self, "authGroup"):
                return []
            else:
                return filter(lambda x: not x.endswith("-pending"), self.authGroup)

        def is_admin(self):
            return bool(filter(lambda x: x.startswith("admin"), self.get_authgroups()))
