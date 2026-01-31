#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf

start() {
	rm -f "${OCR_STOP_DIR}/${OCR_STOP_FILE}"
	exec python3 -u ${OCR_WORK_DIR}/ocr.py
}

stop() {
	touch "${OCR_STOP_DIR}/${OCR_STOP_FILE}"
}

case "$1" in
	start) start ;;
	stop) stop ;;
esac
