#!/usr/bin/python3
import redis

class RedisHook:
    """
        Redis 연결/해제 및 메서드 제공
    """
    def __init__(self, host, port, db, password, **configs):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.conn = None
        self.configs = configs

    def connect(self):
        self.conn = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            **self.configs
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def __getattr__(self, name):
        return getattr(self.conn, name)
