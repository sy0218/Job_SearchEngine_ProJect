#!/usr/bin/python3
from redis.cluster import RedisCluster, ClusterNode

class RedisHook:
    """
        Redis Cluster 연결/해제 및 메서드 제공
    """
    def __init__(self, host,  password, **configs):
        self.redis_node = []
        for node in host.split(","):
            redis_host, redis_port = node.split(":")
            self.redis_node.append(ClusterNode(redis_host, int(redis_port)))
        self.password = password
        self.conn = None
        self.configs = configs

    def connect(self):
        self.conn = RedisCluster(
            startup_nodes = self.redis_node,
            password = self.password,
            **self.configs
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def __getattr__(self, name):
        return getattr(self.conn, name)
