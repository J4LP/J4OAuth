import cPickle
import datetime
import eveapi
import json
import redis
import time
from j4oauth.app import app, db

r = redis.StrictRedis(host=app.config['REDIS'])


class RedisEveAPICacheHandler(object):

    def __init__(self, debug=False):
        self.debug = debug
        self.r = redis.StrictRedis(host=app.config['REDIS'])

    def log(self, what):
        if self.debug:
            print "[%s] %s" % (datetime.datetime.now().isoformat(), what)

    def retrieve(self, host, path, params):
        key = hash((host, path, frozenset(params.items())))

        cached = self.r.get(key)
        if cached is None:
            self.log("%s: not cached, fetching from server..." % path)
            return None
        else:
            cached = cPickle.loads(cached)
            if time.time() < cached[0]:
                self.log("%s: returning cached document" % path)
                return cached[1]
            self.log("%s: cache expired, purging !" % path)
            self.r.delete(key)

    def store(self, host, path, params, doc, obj):
        key = hash((host, path, frozenset(params.items())))
        if obj.cachedUntil == obj.currentTime:
            cachedFor = obj.currentTime + 60 * 15 - obj.currentTime
        else:
            cachedFor = obj.cachedUntil - obj.currentTime
        if cachedFor:
            self.log("%s: cached (%d seconds)" % (path, cachedFor))

            cachedUntil = time.time() + cachedFor
            self.r.set(key, cPickle.dumps((cachedUntil, doc), -1))


def get_character_id(character_name=None):
    if character_name is None:
        raise Exception('No character name provided')
    character_id = r.get('eve:name_id:{}'.format(character_name))
    if character_id is None:
        client = eveapi.EVEAPIConnection(
            cacheHandler=RedisEveAPICacheHandler(debug=app.config['DEBUG']))
        character_id = client.eve.CharacterID(
            names=[character_name]).characters[0]['characterID']
        r.set('eve:name_id:{}'.format(character_name), character_id)
    return character_id


def get_skill(skill_id):
    skill = r.get('eve:skills:{}'.format(skill_id))
    try:
        skill = json.loads(skill)
    except Exception:
        skill = None
    else:
        return skill
    if skill is None:
        client = EveTools()
        skills_groups = client.safe_request('eve/SkillTree').skillGroups
        for skill_group in skills_groups:
            for skill in skill_group.skills:
                if skill['typeID'] == skill_id:
                    _skill = {
                        'skill_id': skill_id,
                        'skill_name': skill['typeName'],
                        'group_name': skill_group['groupName'],
                        'group_id': skill_group['groupID']
                    }
                    r.set('eve:skills:{}'.format(skill_id), json.dumps(_skill))
                    return _skill


class EveTools(object):

    def __init__(self, key_id=None, vcode=None, cache=True):
        if cache:
            self.client = eveapi.EVEAPIConnection(
                cacheHandler=RedisEveAPICacheHandler(
                    debug=app.config['DEBUG']))
        else:
            self.client = eveapi.EVEAPIConnection()
        if key_id and vcode:
            self.auth(key_id, vcode)

    def auth(self, key_id, vcode):
        self.key_id = key_id
        self.vcode = vcode
        self.client = self.client.auth(keyID=key_id, vCode=vcode)
        self.authed = True

    def safe_request(self, request, kwargs=None):
        try:
            req = getattr(self.client, request)
            if kwargs is not None:
                results = req(**kwargs)
            else:
                results = req()
        except eveapi.Error as e:
            app.logger.exception(e)
            raise Exception('API Error, {}'.format(e.message))
        except RuntimeError as e:
            app.logger.exception(e)
            raise Exception('CCP Server Error, {}'.format(e.message))
        except Exception as e:
            app.logger.exception(e)
            raise Exception('System error, our team has been notified !')
        return results

    def check_key(self):
        key_info = self.safe_request('account/APIKeyInfo')
        access_mask, key_type, expires = key_info.key.accessMask, key_info.key.type, key_info.key.expires
        if access_mask != 8388608:
            raise Exception('Invalid access mask')
        if key_type not in ['Character', 'Account']:
            raise Exception('Invalid key type')
        if expires != "":
            raise Exception('Expiration detected on key')
        return True

    def get_characters(self):
        key_info = self.safe_request('account/APIKeyInfo')
        characters = []
        for character in key_info.key.characters:
            characters.append(self.safe_request('eve/CharacterInfo', {'characterID': character['characterID']}))
        return characters

    def get_skills(self, character_id):
        sheet = self.safe_request('char/CharacterSheet', {'characterID': character_id})
        skills = []
        for skill in sheet.skills:
            _skill = get_skill(skill.typeID)
            skills.append(dict(level=skill.level, **_skill))
        return skills

    @staticmethod
    def rowset_to_dict(rowset):
        """
        This method assume it receives a eveapi.Rowset or eveapi.IndexRowset
        and will convert it to a dict for easy serialization.
        """
        result = []
        for row in rowset:
            result.append(EveTools.row_to_dict(row))
        return result

    @staticmethod
    def row_to_dict(row):
        """
        This method assume it receives an eveapi.Row and will convert it
        to a dict for easy serialization.
        """
        result = {}
        for index, key in enumerate(row.__dict__['_cols']):
            if index < len(row.__dict__['_row']):
                if isinstance(row.__dict__['_row'][index], eveapi.IndexRowset):
                    result[key] = EveTools.rowset_to_dict(row.__dict__['_row'][index])
                else:
                    result[key] = row.__dict__['_row'][index]
        return result

    @staticmethod
    def element_to_dict(element):
        """
        This method assume it receives an eveapi.Element and will convert it to
        a dict for easy serialization.
        """
        result = {}
        for key, value in element.__dict__.iteritems():
            if isinstance(value, eveapi.Rowset) or isinstance(
                    value, eveapi.IndexRowset):
                result[key] = EveTools.rowset_to_dict(value)
            else:
                if key not in ('_meta', '_name', '_isrow'):
                    result[key] = value
        return result


    @staticmethod
    def auto_to_dict(resource):
        """
        Easy mode method to detect and convert to dict an eveapi.Resource
        """
        if isinstance(resource, eveapi.Element):
            return EveTools.element_to_dict(resource)
        elif isinstance(resource, eveapi.Row):
            return EveTools.row_to_dict(resource)
        elif isinstance(resource, eveapi.Rowset) \
            or isinstance(resource, eveapi.IndexRowset):
            return EveTools.rowset_to_dict(resource)
        else:
            return None
