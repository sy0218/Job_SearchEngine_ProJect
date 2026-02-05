#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
. /etc/job_project.conf

start() {
	rm -f "${ES_UPLOAD_STOP_DIR}/${ES_UPLOAD_STOP_FILE}"
	exec python3 -u ${ES_UPLOAD_WORK_DIR}/es_upload.py
}

stop() {
	touch "${ES_UPLOAD_STOP_DIR}/${ES_UPLOAD_STOP_FILE}"
}

case "$1" in
	start) start ;;
	stop) stop ;;
esac
