#!/usr/bin/bash

# 공통 env
. /etc/job_project.conf
# 프로젝트 env
. /work/jsy/job_project/conf/job.conf

# 로그 디렉터리 생성 ( 없으면 )
mkdir -p "${HD_EVENT_LOG_DIR}"

cd "${HD_EVENT_WORK_DIR}" || exit 1

exec java -Xms512m -Xmx1g \
    -cp ".:$(hadoop classpath --glob):${JOB_LIB}/*" \
    HdfsCloseWatcher
