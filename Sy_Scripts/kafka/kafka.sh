#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh
. ${Sy_Dir}/Sy_Scripts/conf/server.properties

# 인자가 없거나 공백이면 종료
if [ -z "$1" ]; then
    echo "${0} 인자가 없습니다. (start | stop | status)"
    exit 1
fi


KAFKA_OPT="$1"

case "${KAFKA_OPT}" in
    start|stop)
        for ip in ${kafka_ip}
        do
            log_info "[Kafka] ${ip} systemctl ${KAFKA_OPT}"
            ssh ${ip} "systemctl ${KAFKA_OPT} kafka-server.service"
            echo
        done
        ;;

    status)
        for ip in ${kafka_ip}
        do
            log_info "[Kafka] ${ip} status"
            ssh ${ip} "systemctl status kafka-server | grep Active"
            echo
        done
        ;;

    *)
        echo "지원하지 않는 명령어입니다: ${KAFKA_OPT}"
        echo "사용법: $0 {start|stop|status}"
        exit 1
        ;;
esac
