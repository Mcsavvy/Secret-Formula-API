release: ./make_release
web: gunicorn -c gunicorn.conf.py
worker: celery -A redisflow.app worker -P $CELERY_POOL -c $CELERY_CONCURRENCY -l $CELERY_LOGLEVEL