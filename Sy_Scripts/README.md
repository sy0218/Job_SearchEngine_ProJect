# 💾 Sy_Scripts

- 서버 운영하면서 귀찮아서 만든 **개인 운영용 쉘 스크립트 모음**  
- Kafka, Redis, 서버 점검 등 반복 작업을 자동화하기 위해 작성됨

---
<br>

---
## 📁 디렉터리 구조

```bash
Sy_Scripts/
├── README.md
├── functions.sh          # 공통 함수 모음
├── conf/
│   └── server.properties # 서버 / 서비스 IP 설정
└── *.sh                  # 실제 실행 스크립트
```
---
<br>

## ⚠️ 무조건 필요한 설정 (안 하면 안 됨)
### 1️⃣ 작업 디렉터리 고정
- 모든 스크립트는 아래 파일이 있다고 가정함

```bash
cat /etc/sy_script
Sy_Dir=/work/jsy
```
- 작업 디렉터리 바뀌면 여기만 수정하면 됨
- 스크립트 안에 경로 하드코딩 안 하려고 만든 거
---
### 2️⃣ 모든 스크립트 공통 헤더 (필수)
- 모든 스크립트에 무조건 들어감
```bash
#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh
```
---
<br>

## 🧩 서버 설정 파일
- conf/server.properties
- 서버 IP들 귀찮아서 한 군데 모아둠
```bash
server_ip="192.168.122.59 192.168.122.60 192.168.122.61 192.168.122.62 192.168.122.63 192.168.122.64 192.168.122.65"

zookeeper_ip="192.168.122.60 192.168.122.61 192.168.122.62"

kafka_ip="192.168.122.60 192.168.122.61 192.168.122.62"
kafka_port="9092"

schema_registry="192.168.122.59"
schema_registry_port="8081"
```
- 서버 추가/삭제 → 여기만 고치면 끝
- 스크립트에서 IP 직접 안 씀
---
<br>

## 🛠 공통 함수 (functions.sh)
- 자주쓰는 함수들을 정의 하고 사용
- 예시 살짝만..
```bash
[ap:/work/jsy/Sy_Scripts] cat functions.sh
#!/usr/bin/bash

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
~~
```
---
<br>

## ✍️ 스크립트 작성 예제 ( cmd_all.sh )
```bash
#!/usr/bin/bash
. /etc/sy_script
. ${Sy_Dir}/Sy_Scripts/functions.sh

# 인자 개수 확인
if [ -z "$1" ]; then
    echo "Usage: ${0} <cmd>"
    exit 1
fi

CMD="$1"

## 전역변수 ##
SERVERS=(ap sn1 sn2 sn3 m1 m2 s1)

## CMD 실행 ###
for SERVER in "${SERVERS[@]}";
do
        log_info "[RUN] ${SERVER} BEGIN ${CMD}"
                ssh -o ConnectTimeout=60 "${SERVER}" "${CMD}"
        log_info "[END] ${SERVER} OK ${CMD}"
        echo
        echo
done
```
---
<br>

## ❗ 주의사항 (미래의 나에게)
- 경로 하드코딩 금지 → Sy_Dir 쓰기
- IP 직접 쓰지 말고 server.properties
- echo 말고 log_info / log_error
- 귀찮으면 함수부터 만든다
---
