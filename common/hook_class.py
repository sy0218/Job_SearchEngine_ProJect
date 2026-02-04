#!/usr/bin/python3
from confluent_kafka import Producer, Consumer, TopicPartition, OFFSET_BEGINNING
from confluent_kafka.avro import AvroProducer, AvroConsumer
from confluent_kafka import avro

import redis
import io
import gzip
import json

import psycopg2
from psycopg2.extras import execute_values

import pyarrow.fs as fs

class KafkaHook:
    """
       Kafka 연결/해제 및 메서드 제공
    """
    # 생성자는 브로커 정보만 관리
    def __init__(self, brokers):
        self.brokers = brokers
        self.conn_producer = None
        self.conn_consumer = None

    # =========================
    # Producer
    # =========================
    # 일반 Kafka 프로듀서
    def producer_connect(self, **configs):
        conf = {"bootstrap.servers": self.brokers, **configs}
        self.conn_producer = Producer(conf)

    # Avro Kafka 프로듀서
    def avro_producer_connect(self, schema_registry_url, schema_path, **configs):
        avro_schema = avro.load(schema_path)
        conf = {
            "bootstrap.servers": self.brokers,
            "schema.registry.url": schema_registry_url,
            **configs
        }

        self.conn_producer = AvroProducer(conf, default_value_schema = avro_schema)

    # =========================
    # Consumer
    # =========================
    # 일반 Kafka 컨슈머
    def consumer_connect(self, topic, partition, group_id, **configs):
        conf = {
            "bootstrap.servers": self.brokers,
            "group.id": group_id,
            "enable.auto.commit": False,
            **configs
        }
    
        self.conn_consumer = Consumer(conf)
        self._assign_topic_partition(topic, partition)

    # Avro Kafka 컨슈머
    def avro_consumer_connect(self, topic, partition, group_id, schema_registry_url, **configs):
        conf = {
            "bootstrap.servers": self.brokers,
            "group.id": group_id,
            "schema.registry.url": schema_registry_url,
            "enable.auto.commit": False,
            **configs
        }

        self.conn_consumer = AvroConsumer(conf)
        self._assign_topic_partition(topic, partition)

    # 컨슈머 고정 파티션
    def _assign_topic_partition(self, topic, partition):
        tp = TopicPartition(topic, partition)
        commit = self.conn_consumer.committed([tp])

        tp.offset = (
            commit[0].offset
            if commit and commit[0].offset >= 0
            else OFFSET_BEGINNING
        )

        self.conn_consumer.assign([tp])

    # 프로듀서 Producer
    def produce(self, topic, value):
        if self.conn_producer:
            self.conn_producer.produce(topic=topic, value=value)
    # 프로듀서 버퍼에 남은 메시지 모두 전송
    def flush(self, timeout=30):
        if self.conn_producer:
            self.conn_producer.flush(timeout)

    # 컨슈머 poll
    def poll(self, timeout):
        if self.conn_consumer:
            return self.conn_consumer.poll(timeout)
    # 컨슈머 close
    def close(self):
        if self.conn_consumer:
            self.conn_consumer.close()
    # 컨슈머 commit
    def commit(self, commit_msg):
        if self.conn_consumer:
            self.conn_consumer.commit(commit_msg, asynchronous=False) # 동기적( 정확히 하자! )  

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
            host = self.host,
            port = self.port,
            db = self.db,
            password = self.password,
            **self.configs
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def __getattr__(self, name):
        return getattr(self.conn, name)


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
            host = self.host,
            port = self.port,
            dbname = self.dbname,
            user = self.user,
            password = self.password
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

class HdfsHook:
    """
        HDFS 연결 + 파일 읽기 / 쓰기 메서드 제공
    """
    def __init__(self, host, user):
        self.host = host
        self.user = user
        self.conn = None

    def connect(self):
        self.conn = fs.HadoopFileSystem(host=self.host, user=self.user)

    def read_bytes(self, hdfs_path):
        with self.conn.open_input_file(hdfs_path) as f:
            return f.read()

    def upload_lines(self, hdfs_path, lines):
        with self.conn.open_output_stream(hdfs_path) as f_out:
            for line in lines:
                f_out.write((line + "\n").encode('utf-8'))
