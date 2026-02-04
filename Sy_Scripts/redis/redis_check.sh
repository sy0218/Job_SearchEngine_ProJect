#!/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh

set -e

########################################
# 1. 초기 입력
########################################
read -p "관리할 Redis 컨테이너명을 입력하시오: " CONTAINER_NAME

if [ -z "${CONTAINER_NAME}" ]; then
    log_error "컨테이너명이 입력되지 않았습니다."
    exit 1
fi

if ! docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q "${CONTAINER_NAME}"; then
    log_error "컨테이너 '${CONTAINER_NAME}'이(가) 실행 중이 아니거나 존재하지 않습니다."
    exit 1
fi

read -s -p "Redis 패스워드를 입력하시오: " REDIS_PASS
echo ""

if ! run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" ping | grep -q "PONG"; then
    log_error "Redis 인증 실패 또는 연결 불가!"
    exit 1
fi
log_info "컨테이너 [${CONTAINER_NAME}] 인증 성공."

########################################
# 2. 메인 루프
########################################
while true; do
    echo ""
    echo "------------------------------------------"
    echo " Redis (${CONTAINER_NAME}) 관리 도구"
    echo "------------------------------------------"
    echo "1) 전체 키 조회 (KEYS *)"
    echo "2) 키 값 전체 조회"
    echo "3) 키 데이터 개수 조회"
    echo "4) 일부 조회 (SCAN 계열)"
    echo "5) 특정 값 존재 여부 확인"
    echo "6) 키 삭제 (DEL)"
    echo "7) 키 메모리 사용량 확인"
    echo "8) 현재 DB 전체 키 삭제 (FLUSHDB)"
    echo "q) 종료"
    echo "------------------------------------------"
    read -p "메뉴 번호를 선택하세요: " choice

    [[ "$choice" =~ [qQ] ]] && { log_info "스크립트를 종료합니다."; break; }

    if ! [[ "$choice" =~ ^[1-8]$ ]]; then
        log_error "잘못된 선택입니다."
        continue
    fi

    read -p "작업할 Redis DB 번호를 입력하세요: " DB_NUM
    [ -z "$DB_NUM" ] && { log_error "DB 번호 누락"; continue; }

    if [[ "$choice" =~ ^[2-7]$ ]]; then
        read -p "대상 Redis Key를 입력하세요: " KEY_NAME
        [ -z "$KEY_NAME" ] && { log_error "Key 누락"; continue; }

        KEY_TYPE=$(run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" TYPE "${KEY_NAME}")

        if [[ "$KEY_TYPE" == "none" ]]; then
            log_error "Key '${KEY_NAME}' does not exist."
            continue
        fi

        log_info "Key type: ${KEY_TYPE}"
    fi

########################################
# 3. 메뉴 처리
########################################
    case "$choice" in
        1)
            log_info "DB ${DB_NUM} 전체 키 조회"
            run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" KEYS "*"
            ;;
        2)
            case "$KEY_TYPE" in
                string) run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" GET "${KEY_NAME}" ;;
                hash)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" HGETALL "${KEY_NAME}" ;;
                list)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" LRANGE "${KEY_NAME}" 0 -1 ;;
                set)    run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" SMEMBERS "${KEY_NAME}" ;;
                zset)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" ZRANGE "${KEY_NAME}" 0 -1 WITHSCORES ;;
                *) log_error "지원하지 않는 타입" ;;
            esac
            ;;
        3)
            case "$KEY_TYPE" in
                string) echo "string은 개수 개념이 없습니다." ;;
                hash)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" HLEN "${KEY_NAME}" ;;
                list)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" LLEN "${KEY_NAME}" ;;
                set)    run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" SCARD "${KEY_NAME}" ;;
                zset)   run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" ZCARD "${KEY_NAME}" ;;
            esac
            ;;
        4)
            case "$KEY_TYPE" in
                set)  run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" SSCAN "${KEY_NAME}" 0 ;;
                hash) run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" HSCAN "${KEY_NAME}" 0 ;;
                zset) run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" ZSCAN "${KEY_NAME}" 0 ;;
                *) log_error "SCAN 불가능한 타입" ;;
            esac
            ;;
        5)
            case "$KEY_TYPE" in
                set)
                    read -p "확인할 값(Value): " VALUE
                    run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" SISMEMBER "${KEY_NAME}" "${VALUE}"
                    ;;
                hash)
                    read -p "확인할 필드(Field): " FIELD
                    run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" HEXISTS "${KEY_NAME}" "${FIELD}"
                    ;;
                *) log_error "해당 타입은 존재 여부 확인 불가" ;;
            esac
            ;;
        6)
            read -p "정말 '${KEY_NAME}'을(를) 삭제하시겠습니까? (y/n): " confirm
            if [[ "$confirm" == "y" ]]; then
                run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" DEL "${KEY_NAME}"
                log_info "삭제 완료"
            fi
            ;;
        7)
            RESULT=$(run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" MEMORY USAGE "${KEY_NAME}")
            if [[ -z "$RESULT" || "$RESULT" == "(nil)" ]]; then
                echo "메모리 정보 없음"
            else
                echo "Memory: ${RESULT} bytes"
                echo "≈ $(echo "scale=2; $RESULT/1024" | bc) KB"
                echo "≈ $(echo "scale=2; $RESULT/1024/1024" | bc) MB"
            fi
            ;;
        8)
            log_info "DB ${DB_NUM} 전체 키 삭제 실행 (FLUSHDB)"
            run_redis "${CONTAINER_NAME}" "${REDIS_PASS}" -n "${DB_NUM}" FLUSHDB
            log_info "DB ${DB_NUM} 전체 키 삭제 완료"
            ;;
    esac

    echo ""
    read -p $'\e[32m계속하려면 엔터를 누르세요...\e[0m'
done
