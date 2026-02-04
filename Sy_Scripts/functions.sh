#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/conf/server.properties

# ----------------------------------------
# INFO 로그
# ----------------------------------------
log_info() {
    echo "[INFO ] [$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ----------------------------------------
# ERROR 로그
# ----------------------------------------
log_error() {
    echo "[ERROR] [$(date '+%Y-%m-%d %H:%M:%S')] $*" >&2
}

# ----------------------------------------
# kafka control 함수
# ----------------------------------------
kafka_ctl() {
    local IP="$1"
    local OPT="$2"
    local KAFKA_BIN="${KAFKA_HOME}/bin"
    local KAFKA_CONF="${KAFKA_HOME}/config/server.properties"

    case "${OPT}" in
        start)
            log_info "[Kafka] ${IP} START"
            ssh "${IP}" "${KAFKA_BIN}/kafka-server-start.sh -daemon ${KAFKA_CONF}"
            log_info "[kafka] ${IP} STARTED"
            ;;
        stop)
            log_info "[Kafka] ${IP} STOP"
            ssh "${IP}" "${KAFKA_BIN}/kafka-server-stop.sh"
            log_info "[kafka] ${IP} STOPPED"
            ;;
        status)
            # 원격 서버에서 Kafka 프로세스 체크, 바로 조건문으로 처리
            log_info "[Kafka] ${IP} STATUS"
            if ssh "${IP}" "ps -ef | grep -i 'kafka.Kafka' | grep -v grep" &>/dev/null; then
                log_info "[Kafka] ${IP} is RUNNING..!!"
            else
                log_error "[Kafka] ${IP} is NOT RUNNING..!!"
            fi
            ;;
    esac
}

# ----------------------------------------
# 인자 체크 함수
# ----------------------------------------
check_topic_arg() {
    local TOPIC_NAME="$1"
    local SCRIPT_NAME="$2"

    if [ -z "${TOPIC_NAME}" ]; then
        log_error "이 기능은 토픽명이 인자로 필요합니다."
        echo "사용법: ${SCRIPT_NAME} [토픽명]"
        exit 1
    fi
}

# ----------------------------------------
# Redis 명령 실행 함수 (Docker 기반)
# ----------------------------------------
run_redis() {
    local CONTAINER="$1"
    local PASS="$2"
    shift 2  # 앞의 인자 2개(컨테이너, 비번)를 제거하고 나머지($@)를 명령어 인자로 사용

    docker exec -i "${CONTAINER}" redis-cli -a "${PASS}" "$@" 2>/dev/null
}

# ----------------------------------------
# PostgreSQL 쿼리
# ----------------------------------------
job_sql_exec() {
	PGPASSWORD=$job_PASSWORD psql -h $job_HOST -p $job_PORT -U $job_USER -d $job_DB -c "$1" -At
}
