# -*- coding: utf-8 -*-

import os
import time
from celery import Celery

env=os.environ
CELERY_BROKER_URL=env.get('CELERY_BROKER_URL','redis://localhost:6379'),
CELERY_RESULT_BACKEND=env.get('CELERY_RESULT_BACKEND','redis://localhost:6379')


taskmanager = Celery('extractions',
                    broker=CELERY_BROKER_URL,
                    backend=CELERY_RESULT_BACKEND)


@taskmanager.task(name='extraction.do')
def do(year, format, proj, email, cities):
    time.sleep(10)
    return 'done ! {0} {1} {2} {3} {4}'.format(year, format, proj, email, cities)
