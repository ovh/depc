#!/bin/bash
set -e

CONFIG_FILE='depc.prod.yml'

if [[ $1 ]]; then
  APP_TYPE=$1
fi

if [[ "$APP_TYPE" = "api" || -z $APP_TYPE ]];then

    # Launch Gunicorn
    export G_WORKERS=${G_WORKERS:=5}
    export G_THREADS=${G_THREADS:=1}
    export G_MAX_REQUESTS=${G_MAX_REQUESTS:=1000}
    export G_MAX_REQUESTS_JITTER=${G_MAX_REQUESTS_JITTER:=20}
    export G_BACKLOG=${G_BACKLOG:=5}
    export G_TIMEOUT=${G_TIMEOUT:=300}
    export G_GRACEFUL_TIMEOUT=${G_GRACEFUL_TIMEOUT:=300}

    echo "Starting API"
    exec gunicorn --bind 0.0.0.0:5000 --workers $G_WORKERS \
    --threads $G_THREADS --backlog $G_BACKLOG --timeout $G_TIMEOUT \
    --graceful-timeout $G_GRACEFUL_TIMEOUT --access-logfile - \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(L)ss "%(f)s" "%(a)s"' \
    --max-requests $G_MAX_REQUESTS --max-requests-jitter $G_MAX_REQUESTS_JITTER \
    manage:app

else

    echo "Wrong argument : $APP_TYPE"

fi
