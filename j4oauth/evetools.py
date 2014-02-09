import cPickle
import datetime
import eveapi
import json
import redis
import time
from j4oauth.app import app

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
            # if time.time() < cached[0]:
            #    self.log("%s: returning cached document" % path)
            #    return cached[1]
            return cached[1]
            #self.log("%s: cache expired, purging !" % path)
            # self.r.delete(key)

    def store(self, host, path, params, doc, obj):
        key = hash((host, path, frozenset(params.items())))

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
