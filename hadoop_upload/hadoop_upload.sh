#!/usr/bin/bash

# load env
. /work/jsy/job_project/conf/job.conf
. /work/jsy/job_project/Sy_Scripts/functions.sh
. ${HD_UPLOAD_CONFIG_PATH}

log_info "[RUN] Hadoop Upload Service.."

while true; 
do
	# 초기화
	file_queue=()
	line=0

	# NFS 데이터 파일 시간순 정렬
	mapfile -t files < <(ls -1tr "${NFS_DATA}"/*.ndjson 2>/dev/null)

	for file in "${files[@]}";
	do
		file_mtime=$(stat -c %Y "${file}")
        now_time=$(date +%s)

		# 쓰기중 가능성 확인
		if [ $((now_time - file_mtime)) -lt $(("${DELAY_MIN}" * 60)) ]; then
            break
        fi

		# 라인 세기 & 큐 추가
		line_count=$(wc -l < "${file}")
		file_queue+=("${file}")
		line=$((line + line_count))

		# LINE_LIMIT 도달 시 병합 & 업로드
		if [ "${line}" -ge "${LINE_LIMIT}" ]; then
			upload_file=$(date "+%Y%m%d%H%M%S").gz
            local_gz="${UPLOAD_DIR}/${upload_file}"
            hdfs_gz="${HADOOP_DIR}/${upload_file}"

			log_info "[RUN] hadoop upload 처리 중.. (라인 수: ${line}, 파일: ${#file_queue[@]}개)"

			# 1) 병합 및 압축 ( 실패 시 정리 )
			if ! cat "${file_queue[@]}" | gzip > "${local_gz}"; then
				log_error "로컬 병합 실패.. 정리 후 재시작.."
				rm -f "${local_gz}"
				break
			fi

			# 2) HDFS 전송
			if ! hdfs dfs -copyFromLocal -f "${local_gz}" "${hdfs_gz}"; then
				log_info "하둡 업로드 실패.. 정리 후 재시작.."
				rm -rf "${local_gz}"
				hdfs dfs -rm -f "${hdfs_gz}"
				break
			fi

			# 3) 성공 시 로컬(NFS) 원본 파일 삭제
			log_info "[RUN] hadoop upload 완료.. (라인 수: ${line}, 파일: ${#file_queue[@]}개)"
			for rm_file in "${file_queue[@]}";
			do
				rm -f "${rm_file}"
			done
            break
		fi
	done

	# LINE_LIMIT 미달 시 로그
	if [ "${line}" -lt "${LINE_LIMIT}" ]; then
		log_info "[SKIP] 라인 수 부족.. Retry.. 현재 라인: ${line}"
	fi

	# 스탑 파일 존재시 프로세스 종료
    if [ -f "${HD_UPLOAD_STOP_DIR}/${HD_UPLOAD_STOP_FILE}" ]; then
        log_info "[END] Hadoop Upload Service.. 스탑 파일 확인.."
        break
    fi

    # 루프 대기
    sleep 10

done
