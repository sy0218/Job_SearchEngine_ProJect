#!/usr/bin/bash

# load env
. /work/job_project/conf/job.conf
. /etc/job_project.conf

#exec python3 -u ${ES_UPLOAD_WORK_DIR}/test.py
exec python3 -u ${ES_UPLOAD_WORK_DIR}/es_upload.py
