from os.path import join, dirname

from setuptools import setup, find_packages

setup(
    name='HTTP flood analyzer',
    version='0.0.1',
    packages=find_packages(exclude=["tests.*", "ddos.egg-info"]),
    url='https://justhost.ru/',
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    scripts=['http_protector.py']
)
