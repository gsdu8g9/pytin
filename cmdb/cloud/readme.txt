Cloud management module
=======================

Install
-------

pip install celery
pip install redis


settings.py
-----------

PROXMOX_BACKEND = {
    'MSG_BROKER': 'redis://127.0.0.1:8888/1',
    'MSG_BACKEND': 'redis://127.0.0.1:8888/2'
}
