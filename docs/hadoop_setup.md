# 🐘 Ubuntu에서 Hadoop 3.2.4 설치 & HA 클러스터 구축

---

## 📌 개요
- Ubuntu 환경에서 **Hadoop 3.2.4 클러스터 설치, 노드 설정, 네임노드/리소스 매니저 HA 구성** 가이드
- 클러스터 HA 구성으로 **네임노드 및 리소스 매니저 가용성 확보**

🚀 **Ansible로 자동화된 환경 설정 예시**는 🔗 [`Ansible 레포지토리`](https://github.com/sy0218/Ansible-Multi-Server-Setup)에서 확인하세요!

---
<br>

## ⚙️ 클러스터 서버 구성
| **호스트** | **역할**              | **메모리** | **CPU** |
|------------|--------------------|------------|---------|
| `m1`      | NameNode + DataNode 🟢🔵 | 20G        | 3       |
| `m2`      | NameNode + DataNode 🟢🔵 | 20G        | 3       |
| `s1`      | DataNode 🔵           | 20G        | 3       |

---
<br>

## ⚙️ 환경 변수 설정

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export ZOOKEEPER_HOME=/application/zookeeper
export HADOOP_HOME=/application/hadoop
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export HADOOP_YARN_HOME=$HADOOP_HOME
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_LOG_DIR=/logs/hadoop
export HADOOP_PID_DIR=/var/run/hadoop/hdfs
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export HADOOP_OPTS="-Djava.library.path=$HADOOP_COMMON_LIB_NATIVE_DIR"
export HIVE_HOME=/application/hive
export HIVE_AUX_JARS_PATH=$HIVE_HOME/aux

export PATH=$JAVA_HOME/bin:$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$HIVE_HOME/bin:$HIVE_AUX_JARS_PATH/bin:$ZOOKEEPER_HOME/bin:$PATH

# 적용
source ~/.bashrc
```

---
<br>

## ⚙️ Hadoop 다운로드 및 설치
```bash
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.2.4/hadoop-3.2.4.tar.gz
tar -xzvf hadoop-3.2.4.tar.gz
ln -s /application/hadoop-3.2.4 /application/hadoop
```

---
<br>

## ⚙️ Hadoop 설정 파일
### 🔹 core-site.xml
> 하둡 공통 설정

> HDFS 기본 설정과 HA 클러스터 네임서비스, 주키퍼 연결 정보 등

<details>
<summary>▶️ 클릭하여 보기</summary>

```xml
<configuration>
        <property>
                <name>fs.defaultFS</name>
                <value>hdfs://job-cluster</value>
                <description>네임노드 HA 구성 시 사용할 클러스터 논리적 이름</description>
        </property>

        <property>
                <name>hadoop.http.staticuser.user</name>
                <value>root</value>
                <description>클러스터 기본 사용자</description>
        </property>

        <property>
                <name>hadoop.tmp.dir</name>
                <value>file:///hdfs_tmp/hadoop-${user.name}</value>
                <description>하둡 작업관련 임시 디렉터리</description>
        </property>

        <property>
                <name>ha.zookeeper.quorum</name>
                <value>m1:2181,m2:2181,s1:2181</value>
                <description>주키퍼 노드</description>
        </property>
</configuration>
```
</details>

---

### 🔹 hdfs-site.xml
> HDFS 관련 설정

> HDFS 데이터 디렉터리, HA 네임노드, 저널노드, 자동 장애 전환 등

<details>
<summary>▶️ 클릭하여 보기</summary>

```xml
<configuration>
        <property>
                <name>dfs.nameservices</name>
                <value>job-cluster</value>
                <description>네임서비스 이름</description>
        </property>

        <property>
                <name>dfs.ha.namenodes.job-cluster</name>
                <value>nn1,nn2</value>
                <description>네임노드</description>
        </property>

        <property>
                <name>dfs.namenode.rpc-address.job-cluster.nn1</name>
                <value>m1:9000</value>
                <description>nn1의 RPC 포트</description>
        </property>

        <property>
                <name>dfs.namenode.rpc-address.job-cluster.nn2</name>
                <value>m2:9000</value>
                <description>nn2의 RPC 포트</description>
        </property>

        <property>
                <name>dfs.namenode.http-address.job-cluster.nn1</name>
                <value>m1:50070</value>
                <description>nn1의 UI</description>
        </property>

        <property>
                <name>dfs.namenode.http-address.job-cluster.nn2</name>
                <value>m2:50070</value>
                <description>nn2의 UI</description>
        </property>

        <property>
                <name>dfs.namenode.name.dir</name>
                <value>file:///job/hdfs/nn</value>
                <description>하둡 네임노드 디렉토리</description>
        </property>

        <property>
                <name>dfs.datanode.data.dir</name>
                <value>file:///data1,file:///data2</value>
                <description>하둡 데이터 디렉토리</description>
        </property>

        <property>
                <name>dfs.namenode.shared.edits.dir</name>
                <value>qjournal://m1:8485;m2:8485;s1:8485/job-cluster</value>
                <description>고가용성을 위한 저널노드 지정</description>
        </property>

        <property>
                <name>dfs.journalnode.edits.dir</name>
                <value>/job/hdfs/jn</value>
                <description>고가용성을 위한 저널노드 디렉토리</description>
        </property>

        <property>
                <name>dfs.client.failover.proxy.provider.job-cluster</name>
                <value>org.apache.hadoop.hdfs.server.namenode.ha.ConfiguredFailoverProxyProvider</value>
        </property>

        <property>
                <name>dfs.ha.fencing.methods</name>
                <value>shell(/bin/true)</value>
        </property>

        <property>
                <name>dfs.ha.fencing.ssh.private-key-files</name>
                <value>/root/.ssh/id_rsa</value>
        </property>

        <property>
                <name>dfs.ha.automatic-failover.enabled</name>
                <value>true</value>
        </property>
</configuration>
```
</details>

---

### 🔹 yarn-site.xml
> yarn 관련 설정

> 리소스 매니저, 노드 매니저, HA, 메모리/CPU 제한, FairScheduler 설정

<details>
<summary>▶️ 클릭하여 보기</summary>

```xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
        <description>NodeManager에서 MapReduce shuffle 서비스 실행</description>
    </property>

    <property>
        <name>yarn.nodemanager.aux-services.mapreduce.shuffle.class</name>
        <value>org.apache.hadoop.mapred.ShuffleHandler</value>
        <description>ShuffleHandler 클래스 지정</description>
    </property>

    <property>
        <name>yarn.nodemanager.vmem-check-enabled</name>
        <value>false</value>
        <description>가상메모리 검사 비활성화 (작은 클러스터에서 권장)</description>
    </property>

    <property>
        <name>yarn.nodemanager.pmem-check-enabled</name>
        <value>false</value>
        <description>물리메모리 검사 비활성화</description>
    </property>

    <property>
        <name>yarn.nodemanager.resource.memory-mb</name>
        <value>10240</value>
        <description>NodeManager가 관리할 총 메모리 (20G 서버에서 10G 사용)</description>
    </property>

    <property>
        <name>yarn.nodemanager.resource.cpu-vcores</name>
        <value>3</value>
        <description>NodeManager가 관리할 CPU 코어 수 (서버 코어 수 기준)</description>
    </property>

    <property>
        <name>yarn.scheduler.minimum-allocation-mb</name>
        <value>1024</value>
        <description>YARN에서 ResourceRequest 최소 메모리 단위 (1G)</description>
    </property>

    <property>
        <name>yarn.scheduler.maximum-allocation-mb</name>
        <value>5120</value>
        <description>YARN에서 ResourceRequest 최대 메모리 단위 (5G)</description>
    </property>

    <property>
        <name>yarn.resourcemanager.scheduler.class</name>
        <value>org.apache.hadoop.yarn.server.resourcemanager.scheduler.fair.FairScheduler</value>
        <description>Fair Scheduler 사용</description>
    </property>

    <property>
        <name>yarn.scheduler.fair.allocation.file</name>
        <value>/application/hadoop/etc/hadoop/fair-scheduler.xml</value>
        <description>Fair Scheduler Pool 정의 파일 경로</description>
    </property>

    <property>
        <name>yarn.resourcemanager.ha.enabled</name>
        <value>true</value>
        <description>ResourceManager HA 활성화</description>
    </property>

    <property>
        <name>yarn.resourcemanager.ha.rm-ids</name>
        <value>rm1,rm2</value>
        <description>HA RM ID 리스트</description>
    </property>

    <property>
        <name>yarn.resourcemanager.hostname.rm1</name>
        <value>m1</value>
        <description>RM1 호스트 이름</description>
    </property>

    <property>
        <name>yarn.resourcemanager.hostname.rm2</name>
        <value>m2</value>
        <description>RM2 호스트 이름</description>
    </property>

    <property>
        <name>yarn.resourcemanager.webapp.address.rm1</name>
        <value>m1:8088</value>
        <description>RM1 웹 UI 주소</description>
    </property>

    <property>
        <name>yarn.resourcemanager.webapp.address.rm2</name>
        <value>m2:8088</value>
        <description>RM2 웹 UI 주소</description>
    </property>

    <property>
        <name>yarn.resourcemanager.cluster-id</name>
        <value>job-cluster</value>
        <description>클러스터 ID</description>
    </property>

    <property>
        <name>yarn.resourcemanager.zk-address</name>
        <value>m1:2181,m2:2181,s1:2181</value>
        <description>YARN HA Zookeeper 주소 (RM 상태 저장)</description>
    </property>

    <property>
        <name>yarn.resourcemanager.store.class</name>
        <value>org.apache.hadoop.yarn.server.resourcemanager.recovery.ZKRMStateStore</value>
        <description>RM 상태 복구 클래스 (ZK 사용)</description>
    </property>

    <property>
        <name>yarn.client.failover-proxy-provider</name>
        <value>org.apache.hadoop.yarn.client.ConfiguredRMFailoverProxyProvider</value>
        <description>클라이언트 RM HA failover 프로바이더</description>
    </property>

    <property>
        <name>yarn.resourcemanager.recovery.enabled</name>
        <value>true</value>
        <description>RM HA 상태 복구 활성화</description>
    </property>
</configuration>
```
</details>

---

### 🔹 yarn-env.sh
> yarn 환경변수 설정

<details>
<summary>▶️ 클릭하여 보기</summary>

```bash
export YARN_RESOURCEMANAGER_HEAPSIZE=10240
```
</details>

---

### 🔹 hadoop-env.sh
> Hadoop 환경변수 설정

<details>
<summary>▶️ 클릭하여 보기</summary>

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HEAPSIZE_MAX=10240
export HADOOP_HEAPSIZE_MIN=1024
```
</details>

---

### 🔹 workers
> 노드매니저 + 데이터노드 실행 호스트 목록

<details>
<summary>▶️ 클릭하여 보기</summary>

```text
m1
m2
s1
```
</details>

---

### 🔹 fair-scheduler.xml
> YARN FairScheduler 정책 설정

<details>
<summary>▶️ 클릭하여 보기</summary>

```xml
<?xml version="1.0"?>
<allocations>
  <user name="root">
    <maxRunningApps>5</maxRunningApps>
  </user>
</allocations>
```
</details>

---

### 🔹 hadoop-config.sh
> Hadoop 사용자 환경 변수

<details>
<summary>▶️ 클릭하여 보기</summary>

```bash
export HDFS_NAMENODE_USER=root
export HDFS_DATANODE_USER=root
export HDFS_SECONDARYNAMENODE_USER=root
export YARN_RESOURCEMANAGER_USER=root
export YARN_NODEMANAGER_USER=root
export HDFS_ZKFC_USER=root
export HDFS_JOURNALNODE_USER=root
```
</details>

---
<br>

## ⚙️ Hadoop HA 클러스터 기동
### 🔹 Master (m1)
```bash
hdfs zkfc -formatZK       # ZK Failover Controller용 ZooKeeper 초기화
start-dfs.sh               # HDFS(NameNode, DataNode) 시작
hdfs namenode -format      # NameNode 메타데이터 초기화 (첫 실행 시)
stop-dfs.sh                # HDFS 잠시 중지 (초기화 후 재시작 준비)
start-all.sh               # HDFS + YARN 전체 클러스터 시작
```
---
### 🔹 Master2 (m2)
```bash
hdfs namenode -bootstrapStandby  # Standby NameNode 초기 동기화
hadoop-daemon.sh start namenode  # Standby NameNode 시작
yarn-daemon.sh start resourcemanager # YARN ResourceManager 시작
```

---
<br>

## 🔍 HA 상태 확인
### 🔹 네임노드
```bash
hdfs haadmin -getServiceState nn1  # active
hdfs haadmin -getServiceState nn2  # standby
```
---
### 🔹 리소스매니저
```bash
yarn rmadmin -getServiceState rm1  # standby
yarn rmadmin -getServiceState rm2  # active
```

---
<br>

## 🔍 최종 확인
```bash
hdfs dfsadmin -report
```
```nginx
# 예시 출력
Configured Capacity: 31178293248 (29.04 GB)
Present Capacity: 29466746880 (27.44 GB)
DFS Remaining: 29466599424 (27.44 GB)
DFS Used: 147456 (144 KB)
DFS Used%: 0.00%
Live datanodes (3):
  Name: 192.168.122.63:9866 (m1)
  Name: 192.168.122.64:9866 (m2)
  Name: 192.168.122.65:9866 (s1)
```

---
<br>

## ✅ 참고 사항
- **HA 구성 필수**: NameNode와 ResourceManager를 HA로 구성해야 클러스터 가용성 확보 가능.
- **노드별 역할 구분**:  
  - `m1`, `m2` → NameNode + DataNode  
  - `s1` → DataNode 전용  
- **HDFS 및 YARN 디렉터리**:  
  - `dfs.namenode.name.dir`, `dfs.datanode.data.dir`, `dfs.journalnode.edits.dir` 경로는 **존재하고 쓰기 권한** 필요.
- **ZooKeeper 의존성**:  
  - HA NameNode와 RM HA 설정 시 **ZooKeeper quorum** (`ha.zookeeper.quorum` / `yarn.resourcemanager.zk-address`) 정상 동작 필요.
- **Hadoop 사용자 환경**:  
  - `HDFS_NAMENODE_USER`, `HDFS_DATANODE_USER`, `YARN_RESOURCEMANAGER_USER` 등 모든 데몬 사용자는 **root 또는 권한 있는 계정**으로 지정.
- **클러스터 시작 순서**:  
  1. ZooKeeper 시작  
  2. NameNode/JournalNode 포맷 및 시작  
  3. DataNode, ResourceManager, NodeManager 시작  
- **Standby NameNode 초기화**: `hdfs namenode -bootstrapStandby` 반드시 수행.
- **YARN 리소스 제한**:  
  - NodeManager 메모리/CPU 설정 (`yarn.nodemanager.resource.memory-mb`, `yarn.nodemanager.resource.cpu-vcores`) 적절히 조정.
- **FairScheduler 사용 시**: `fair-scheduler.xml`에서 사용자별 최대 실행 애플리케이션 수 제한 가능.
- **서비스 자동화**:  
  - `systemd` 서비스 또는 스크립트 등록 시 서버 재부팅 후 **자동 시작 및 관리** 가능.
- **HA 상태 확인**:  
  - NameNode: `hdfs haadmin -getServiceState <nn>`  
  - ResourceManager: `yarn rmadmin -getServiceState <rm>`
- **최종 확인**:  
  - `hdfs dfsadmin -report` 로 클러스터 용량, 사용량, DataNode 상태 점검.
- **주의**:  
  - HDFS 포맷(`hdfs namenode -format`)은 **첫 실행 시만** 수행, 이미 운영 중인 데이터는 삭제됨.  
  - 클러스터 재시작 시 NameNode/RM active/standby 상태 확인 필수.  
  - HA failover, fencing, ZK 설정 정확히 입력하지 않으면 자동 장애 전환 실패 가능.
---
