from concurrent.futures import ProcessPoolExecutor, as_completed
from common.job_class import Get_env, Get_properties, StopChecker
from common.hook_class import KafkaHook

import easyocr, os, warnings, time

from conf.config_log import setup_logger
logger = setup_logger(__name__)

os.environ["PYTORCH_NO_CUDA_MEMORY_CACHING"] = "1"
warnings.filterwarnings("ignore")


# ===============================
# 각 워커 프로세스의 독립적인 자원 풀
# ===============================
worker_context = {"ocr_reader": None, "properties": None}

# ===============================
# 워커 초기화: 프로세스 시작 시 OCR Reader 객체와 설정 로드
# ===============================
def init_worker(config_path):
    worker_context["properties"] = Get_properties(config_path)
    worker_context["ocr_reader"] = easyocr.Reader(['ko','en'], gpu=False) # gpu 없음 ㅠㅠ
    logger.info(f"OCR Worker 초기화 성공 (PID: {os.getpid()})")

# ===============================
# 이미지 처리 (OCR)
# ===============================
def process_message(img_path):
    props = worker_context["properties"]
    img_reader = worker_context["ocr_reader"]

    try:
        img_text = img_reader.readtext(img_path)
        text = " ".join([r[1] for r in img_text if r[2] >= float(props["ocr"]["confidence"])])
        return {"img_path": img_path, "text": text}
    except Exception as e:
        logger.error(f"OCR 처리 실패: {img_path} {e}")
        raise

# ===============================
# Future 결과 수집
# ===============================
def collect_results(futures):
    results = []
    for future in as_completed(futures, timeout=300):
        results.append(future.result())
    return results


# ===============================
# Main 함수
# ===============================
def _main():
    # ===============================
    # 환경 변수 및 설정 로드
    # ===============================
    ocr_env = Get_env._ocr()
    kafka_env = Get_env._kafka()
    nfs_env = Get_env._nfs()
    properties = Get_properties(ocr_env["config_path"])
    poll_size = int(properties["poll_opt"]["poll_size"])
    logger.info("환경 변수 및 설정 로드 완료")

    # ===============================
    # Kafka + consumer + 일반
    # ===============================
    kafka_consumer = KafkaHook(kafka_env["kafka_host"])
    kafka_consumer.consumer_connect(
        kafka_env["ocr_topic"], int(properties["partition_num"]["num"]),
        kafka_env["ocr_group_id"]
    )
    logger.info("Kafka Consumer 연결 완료")

    try:
        # ===============================
        # ProcessPoolExecutor 로 OCR 멀티프로세스 처리
        # ===============================
        with ProcessPoolExecutor(
            max_workers=poll_size,
            initializer=init_worker,
            initargs=(ocr_env["config_path"],)
        ) as executor:

            while True:
                batch = []
                while len(batch) < poll_size:
                    msg = kafka_consumer.poll(3.0)
                    if msg is None:
                        logger.info(f"[INFO] 아직 메시지 없음!  현재 batch size: {len(batch)}.. 30초 대기..")
                        time.sleep(30)
                        continue
                    batch.append(msg)

                offset_info = f"partition-{batch[0].partition()} : {batch[0].offset()} ~ {batch[-1].offset()}"
                logger.info(f"==== 배치 병렬 처리 시작.. {offset_info} ====")

                # 메시지를 각 워커에 할당
                futures = []
                for m in batch:
                    img_hash = m.value().decode('utf-8')
                    img_path = os.path.join(
                        nfs_env["nfs_img"],
                        img_hash[0] + img_hash[1],
                        img_hash[2] + img_hash[3],
                        img_hash
                    )
                    print(img_path)
                    futures.append(executor.submit(process_message, img_path))

                results = collect_results(futures)
                for r in results:
                    print(r["img_path"])
                    print(r["text"])
                    print()

                # kafka 오프셋 커밋
                #kafka.commit(batch[-1])
                logger.info(f"==== 배치 병렬 처리 완료.. {offset_info} ====")

                # Stop file 체크
                if StopChecker._job_stop(ocr_env["stop_dir"], ocr_env["stop_file"]):
                    logger.warning("Stop 파일 감지 → 종료 프로세스 진입")
                    break

                time.sleep(3)
    except Exception as e:
        logger.error("Ocr 실행 중 오류 발생, 모든 배치 중단", exc_info=True)
    finally:
        kafka_consumer.close()
        logger.info("프로세스 종료. 모든 자원 반납 완료.")
if __name__ == "__main__":
    _main()
