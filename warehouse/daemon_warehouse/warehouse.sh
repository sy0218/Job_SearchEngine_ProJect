#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
. /etc/job_project.conf

start() {
	rm -f "${WAREHOUSE_STOP_DIR}/${WAREHOUSE_STOP_FILE}"
	exec python3 -u ${WAREHOUSE_WORK_DIR}/warehouse.py
}

stop() {
	touch "${WAREHOUSE_STOP_DIR}/${WAREHOUSE_STOP_FILE}"
}

case "$1" in
	start) start ;;
	stop) stop ;;
esac
