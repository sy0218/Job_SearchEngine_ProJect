#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
#exec python3 -u ${WAREHOUSE_WORK_DIR}/test.py
exec python3 -u ${WAREHOUSE_WORK_DIR}/warehouse.py
