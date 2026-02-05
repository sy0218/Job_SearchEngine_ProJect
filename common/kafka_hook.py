#!/usr/bin/python3
from confluent_kafka import Producer, Consumer, TopicPartition, OFFSET_BEGINNING
from confluent_kafka.avro import AvroProducer, AvroConsumer
from confluent_kafka import avro

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
        self.conn_producer = AvroProducer(conf, default_value_schema=avro_schema)

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
