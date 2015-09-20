from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='ddos',
    version='0.0.1',
    packages=find_packages(exclude=["directadmin.*", "directadmin"]),
    long_description=open(join(dirname(__file__), 'README.txt')).read(),
)
