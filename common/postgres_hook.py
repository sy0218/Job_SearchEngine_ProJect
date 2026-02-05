#!/usr/bin/python3
import psycopg2
from psycopg2.extras import execute_values

class PostgresHook:
    """
        PostgreSQL 연결 및 CRUD 메서드 제공
    """
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = None
        self.cur = None

    def connect(self):
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        self.cur = self.conn.cursor()

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def fetchone(self, sql, params=None):
        self.cur.execute(sql, params)
        return self.cur.fetchone()

    def execute(self, sql, params=None, commit=False):
        self.cur.execute(sql, params)
        if commit:
            self.conn.commit()

    def __getattr__(self, name):
        return getattr(self.conn, name)
