from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='ddos',
    version='0.0.1',
    packages=find_packages(exclude=["tests.*", "ddos.egg-info"]),
    url='https://justhost.ru/'
    long_description=open(join(dirname(__file__), 'README.txt')).read(),
    scripts = ['http_protector.py'],
)
