#!/usr/bin/env bash
set -euo pipefail

redis-server /server/app/support/redis.conf &
redis_pid=$!

# Wait until Redis accepts connections before starting Celery.
for _ in $(seq 1 100); do
	if redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
		break
	fi
	sleep 0.1
done

if ! redis-cli -h 127.0.0.1 -p 6379 ping >/dev/null 2>&1; then
	echo "redis-server did not become ready" >&2
	exit 1
fi

reports_directory=${DIRECTORY_REPORTS:-/server/reports}
celery_log_directory="$(dirname "${reports_directory}")/reports_webhook"
mkdir -p "${celery_log_directory}"

celery -A app.util_celery_tasks worker --loglevel=INFO --logfile="${celery_log_directory}/logger_uvicorn-celery-worker.txt" --pool=solo --concurrency=1 &
celery_worker_pid=$!

celery -A app.util_celery_tasks beat --loglevel=INFO --logfile="${celery_log_directory}/logger_uvicorn-celery-tasks.txt" &
celery_beat_pid=$!

uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-keyfile=${SSL_KEY} --ssl-certfile=${SSL_CERT} &
uvicorn_pid=$!

# If either child exits, stop the other and exit non-zero so compose can restart.
wait -n "$redis_pid" "$celery_worker_pid" "$celery_beat_pid" "$uvicorn_pid"

exit 1
