#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh

# ===========================
# 전역변수
# ===========================
LOG_DIR="/work/jsy/job_project/logs"
RETENTION_DAYS=5

# ===========================
# 삭제 로직
# ===========================
log_info "[RUN] 로그 삭제 시작: ${LOG_DIR}, 보관기간: ${RETENTION_DAYS}일"

if [ -d "$LOG_DIR" ]; then
    find "${LOG_DIR}" -type f -mtime +${RETENTION_DAYS} -print -exec rm -f {} \;
    log_info "[END] 로그 삭제 완료"
else
    log_info "[ERROR] 디렉토리가 존재하지 않습니다: ${LOG_DIR}"
fi

