"""Class for handling user alert logic. Sending and getting."""

from flask_redis import FlaskRedis


class Alert(object):
    def __init__(self, user, app):
        self.user = user
        self.redis_store = FlaskRedis(app)

    def get(self):
        try:
            alerts = self.redis_store.lrange(self.user.userhash(), 0, -1)
        except Exception as e:
            alerts = ['Alert: Could not retreive alert for user']
            print("Problem retreiving alerts {error}").format(error=e)
        return alerts

    def set(self, channel, message):
        try:
            self.redis_store.lpush(channel, message)
        except Exception as e:
            print("Problem setting alerts {error}").format(error=e)
