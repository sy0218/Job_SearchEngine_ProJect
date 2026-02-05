#!/usr/bin/python3
import pyarrow.fs as fs

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
