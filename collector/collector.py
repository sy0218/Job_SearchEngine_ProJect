#!/usr/bin/python3
from conf.config_log import setup_logger
from common.job_class import Get_env, Get_properties, StopChecker, DataPreProcessor
from common.crawling_class import ChromeDriver, JobParser
from common.hook_class import RedisHook, KafkaHook

import sys, time
logger = setup_logger(__name__)

def _main():
    """
    메인 수집 로직
    - 웹 크롤링
    - Redis 중복 체크
    - Kafka Avro Producer 전송
    """

    def _get_xpaths(domain, job_type):
        """
        도메인 + 직무 타입별 XPath 정보 반환
        """
        return {
            "response": properties["xpath"][f"{domain}.response.{job_type}"],
            "href": properties["xpath"][f"{domain}.href.{job_type}"],
            "company": properties["xpath"][f"{domain}.company.{job_type}"],
            "title": properties["xpath"][f"{domain}.title.{job_type}"],
            "wait": properties["xpath"][f"{domain}.wait.{job_type}"]
        }

    try:
        # ===============================
        # 환경 변수 및 설정 로드
        # ===============================
        collector_env = Get_env._collector()
        redis_env = Get_env._redis()
        kafka_env = Get_env._kafka()
        properties = Get_properties(collector_env["config_path"])

        logger.info("환경 변수 및 설정 로드 완료")

        # ===============================
        # Redis 연결 (중복 데이터 체크용)
        # ===============================
        redis = RedisHook(
            redis_env["redis_host"],
            redis_env["redis_port"],
            redis_env["redis_job_db"],
            redis_env["redis_password"]
        )
        redis.connect()
        logger.info("Redis 연결 완료")

        # ===============================
        # Kafka + Schema Registry 연결
        # ===============================
        kafka = KafkaHook(kafka_env["kafka_host"])
        kafka.avro_producer_connect(
            kafka_env["schema_registry"],
            properties["schema"]["job_header"]
        )
        logger.info("Kafka Avro Producer 연결 완료")

        # ===============================
        # Chrome 브라우저 기동
        # ===============================
        browser = ChromeDriver()
        logger.info("ChromeDriver 시작")

        domain_lst = properties["domain"]["catagory"].split(',')
        job_count = int(properties["job_catagory_count"]["count"])

        # ===============================
        # 메인 수집 루프
        # ===============================
        while True:
            for domain in domain_lst:
                for number in range(1, job_count + 1):

                    job_type = properties["url_number"][f"url{number}"]
                    job_url = properties["url"][f"{domain}.url.{job_type}"]
                    xpaths = _get_xpaths(domain, job_type)

                    logger.info(f"수집 시작 | domain={domain}, job_type={job_type}")
                    logger.debug(f"접속 URL: {job_url}")

                    # 페이지 접속 및 스크롤
                    browser.get(job_url)
                    browser.wait_css(xpaths["wait"], 10)
                    browser.autoscroll(xpaths["wait"], 10, 1, 3)

                    parser = JobParser(browser)
                    response = parser.get_response()

                    redis_pipe = redis.pipeline(transaction=False)
                    job_headers = []
                    # ===============================
                    # 채용 공고 파싱
                    # ===============================
                    for job_html in response.xpath(xpaths["response"]):
                        job_header = parser.get_job(
                            domain,
                            job_html,
                            xpaths["href"],
                            xpaths["company"],
                            xpaths["title"]
                        )

                        # href 기준 해시 (중복 판별 키)
                        href_hash = DataPreProcessor._hash(job_header["href"] + job_header["title"])

                        # msgid 필드에 href_hash 추가
                        job_header["msgid"] = href_hash

                        # Redis pipeline 적재 및 채용공고 헤더 수집
                        redis_pipe.sadd(redis_env["redis_jobhead_key"], href_hash)
                        job_headers.append(job_header)

                    # Redis 전송
                    redis_info = redis_pipe.execute()
                    # ===============================
                    # Redis 중복 체크 처리
                    # ===============================
                    for job_header, flag in zip(job_headers, redis_info):
                        if flag == 0:
                            logger.debug(
                                f"중복 데이터 스킵 (Redis) | href={job_header['href']}"
                            )
                        else:
                            # ===============================
                            # Kafka 전송 ( Avro 직렬화)
                            # ===============================
                            kafka.produce(
                                topic=kafka_env["job_topic"],
                                value=job_header
                            )
                            logger.info(
                                f"Kafka 전송 완료 | topic={kafka_env['job_topic']} | company={job_header['company']} | title={job_header['title']}"
                            )

                    # 프로듀서 버퍼에 남은 메시지 모두 전송
                    kafka.flush()                    

                    # ===============================
                    # 종료 플래그 체크
                    # ===============================
                    if StopChecker._job_stop(
                        collector_env["stop_dir"],
                        collector_env["stop_file"]
                    ):
                        logger.warning("Stop 파일 감지 → Collector 종료")
                        sys.exit(0)

                    time.sleep(3)

    except Exception as e:
        logger.error("Collector 실행 중 오류 발생", exc_info=True)

    finally:
        # ===============================
        # 리소스 정리
        # ===============================
        browser.quit()
        redis.close()
        kafka.flush()
        logger.info("Collector 정상 종료")


if __name__ == "__main__":
    _main()
