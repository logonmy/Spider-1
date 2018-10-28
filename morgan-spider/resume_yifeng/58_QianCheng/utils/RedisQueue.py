#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: wuyue92tree@163.com

import redis


class RedisQueue(object):
    """Simple Queue with Redis Backend"""

    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

    def clean(self):
        """Empty key"""
        return self.__db.delete(self.key)


class RedisSet(object):
    """Simple Deduplicate with Redis Backend"""

    def __init__(self, name, namespace='deduplicate', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' % (namespace, name)

    def sadd(self, item):
        """Return the approximate size of the queue."""
        if self.__db.sadd(self.key, item) == 0:
            return False
        else:
            return True

    def scard(self):
        """Return True if the queue is empty, False otherwise."""
        return self.__db.scard(self.key)

    def clean(self):
        """Empty key"""
        return self.__db.delete(self.key)


class RedisHash(object):
    """Simple Hash with Redis Backend"""

    def __init__(self, name, **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        self.key = name

    def hget(self, item):
        """Return the approximate size of the queue."""
        return self.__db.hget(self.key, item)

    def hset(self, item, value):
        """Return True if the queue is empty, False otherwise."""
        return self.__db.hset(self.key, item, value)

    def hexists(self, item):
        return self.__db.hexists(self.key, item)

    def clean(self):
        """Empty key"""
        return self.__db.delete(self.key)
