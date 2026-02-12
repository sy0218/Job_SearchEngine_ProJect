#!/usr/bin/python3
import os, configparser, random, hashlib, json, io, gzip, re
from pathlib import Path

class Get_env:
    @staticmethod
    def _collector():
        return {
            "config_path": os.environ["COLLECTOR_CONFIG_PATH"],
            "stop_dir": os.environ["COLLECTOR_STOP_DIR"],
            "stop_file": os.environ["COLLECTOR_STOP_FILE"]
        }

    @staticmethod
    def _consumer():
        return {
            "config_path": os.environ["CONSUMER_CONFIG_PATH"],
            "stop_dir": os.environ["CONSUMER_STOP_DIR"],
            "stop_file": os.environ["CONSUMER_STOP_FILE"]
        }

    @staticmethod
    def _ocr():
        return {
            "config_path": os.environ["OCR_CONFIG_PATH"],
            "stop_dir": os.environ["OCR_STOP_DIR"],
            "stop_file": os.environ["OCR_STOP_FILE"]
        }

    @staticmethod
    def _warehouse():
        return {
            "config_path": os.environ["WAREHOUSE_CONFIG_PATH"],
            "stop_dir": os.environ["WAREHOUSE_STOP_DIR"],
            "stop_file": os.environ["WAREHOUSE_STOP_FILE"]
        }

    @staticmethod
    def _es_upload():
        return {
            "config_path": os.environ["ES_UPLOAD_CONFIG_PATH"],
            "stop_dir": os.environ["ES_UPLOAD_STOP_DIR"],
            "stop_file": os.environ["ES_UPLOAD_STOP_FILE"]
        }

    @staticmethod
    def _redis():
        return {
            "redis_host": os.environ["REDIS_HOST"],
            "redis_password": os.environ["REDIS_PASSWORD"],
            "redis_jobhead_key": os.environ["REDIS_JOBHEAD_KEY"]
        }

    @staticmethod
    def _kafka():
        return {
            "kafka_host": os.environ["KAFKA_HOST"],
            "schema_registry": os.environ["SCHEMA_REGISTRY"],
            "job_topic": os.environ["JOB_TOPIC"],
            "job_group_id": os.environ["JOB_GROUP_ID"],
            "ocr_topic": os.environ["OCR_TOPIC"],
            "ocr_group_id": os.environ["OCR_GROUP_ID"]
        }

    @staticmethod
    def _postgres():
        return {
            "pg_host": os.environ["POSTGRESQL_HOST"],
            "pg_port": os.environ["POSTGRESQL_PORT"],
            "pg_db": os.environ["POSTGRESQL_DB"],
            "pg_user": os.environ["POSTGRESQL_USER"],
            "pg_password": os.environ["POSTGRESQL_PASSWORD"]
        }

    @staticmethod
    def _es():
        return {
            "es_host": os.environ["ES_HOST"],
            "job_index": os.environ["ES_JOB_INDEX"]
        }

    @staticmethod
    def _hadoop():
        return {
            "hadoop_fs_name": os.environ["HADOOP_FS_NAME"],
            "hadoop_user": os.environ["HADOOP_USER"]    
        }

    @staticmethod
    def _nfs():
        return {
            "nfs_data": os.environ["NFS_DATA"],
            "nfs_img": os.environ["NFS_IMG"]
        }


class Get_properties:
    def __init__(self, config_path):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.optionxform = str
        self.config.read(config_path)

    def __getitem__(self, section):
        return self.config[section]

class StopChecker:
    @staticmethod
    def _job_stop(stop_dir, stop_file):
        stop_path = os.path.join(stop_dir, stop_file)
        return os.path.exists(stop_path)

class DataPreProcessor:
    @staticmethod
    def _hash(data):
        """
            data를 SHA1 해시로 변경
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    @staticmethod
    def _dict_to_ndjson(dict_lst):
        """
            딕셔너리 리스트 → NDJSON 문자열로 변환
            각 딕셔너리를 한 줄씩 JSON으로 직렬화
        """
        return "\n".join(json.dumps(d, ensure_ascii=False) for d in dict_lst) + "\n"

    @staticmethod
    def _decompress_gzip_bytes(data):
        """
            gzip 압축된 bytes 데이터를 받아 → UTF-8 문자열로 변환하여 반환
        """
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            file_bytes = gz.read()
        return file_bytes.decode("utf-8")

    @staticmethod
    def _clean_ocr_text(text_lst):
        """
            이미지 텍스트 배열을 받아 → 전처리 후 유효한 텍스트만 배열로 반환 
        """
        clean = []
        for text in text_lst:
            text = re.sub(r'[^가-힣a-zA-Z0-9\s/~.]+', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
            clean.append(text)
        return clean

    @staticmethod
    def _get_es_action(index, doc_id):
        """
            Elasticsearch Bulk용 action 메타 추출
            - index : 업로드할 인덱스명
            - doc_id : 문서 ID
        """
        action = {"index": {"_index": index, "_id": doc_id}}
        return json.dumps(action, ensure_ascii=False)
        

class CopyToLocal:
    """
    주어진 경로에 데이터를 저장
    - 경로는 튜플로 받음 : ('/nfs', '2a', 'a9', '2aa9asdfi23kludasui~')
    - 파일명은 튜플 마지막 요소로 사용
    """

    @staticmethod
    def save(path, data):
        full_dir = Path(*path[:-1])
        full_dir.mkdir(parents=True, exist_ok=True)
        file_path = full_dir / path[-1]

        if not file_path.exists(): # 파일이 없을 떄만 저장
            with open(file_path, "wb") as f:
                f.write(data)
        else:
            pass

        return str(file_path.resolve())
