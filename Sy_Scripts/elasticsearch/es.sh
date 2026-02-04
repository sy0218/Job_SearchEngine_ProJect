#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh
. ${Sy_Dir}/Sy_Scripts/conf/server.properties

# 인자가 없거나 공백이면 종료
if [ -z "$1" ]; then
    echo "${0} 인자가 없습니다. (start | stop | status)"
    exit 1
fi


ES_OPT="$1"

case "${ES_OPT}" in
    start|stop)
        for ip in ${es_ip}
        do
            log_info "[Elasticsearch] ${ip} systemctl ${ES_OPT}"
            ssh ${ip} "systemctl ${ES_OPT} elasticsearch.service"
            echo
        done
        ;;

    status)
        for ip in ${es_ip}
        do
            log_info "[Elasticsearch] ${ip} status"
            ssh ${ip} "systemctl status elasticsearch.service | grep Active"
            echo
        done
        ;;

    *)
        echo "지원하지 않는 명령어입니다: ${ES_OPT}"
        echo "사용법: $0 {start|stop|status}"
        exit 1
        ;;
esac
