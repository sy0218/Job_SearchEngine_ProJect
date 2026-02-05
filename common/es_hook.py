#!/usr/bin/python3
from elasticsearch import Elasticsearch, helpers

class ElasticsearchHook:
    """
        Elasticsearch 연결만 제공하는 Hook
    """
    def __init__(self, hosts, timeout):
        """
        hosts : 리스트 ["ip1:9200", "ip2:9200", ...]
        timeout : 요청 타임아웃
        """
        self.hosts = hosts
        self.timeout = timeout
        self.conn = None

    def connect(self):
        self.conn = Elasticsearch(self.hosts)
        self.conn = self.conn.options(request_timeout=self.timeout)

    def bulk_upload(self, actions, chunk_size):
        success, failed = helpers.bulk(
            client = self.conn,
            actions = actions,
            chunk_size = chunk_size,
            stats_only = True
        )
        return success, failed

    def close(self):
        self.conn.close()
