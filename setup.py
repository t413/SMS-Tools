import os
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='smstools',
    version='0.1.0',
    description='Universal SMS conversion tool',
    long_description=read('README.rst'),
    author='Tim O\'Brien',
    author_email='timo@t413.com',
    packages=['smstools', 'smstools.tests'],
    scripts=['bin/smstools'],
    url='https://github.com/t413/SMS-Tools',
    license='CC BY-NC-SA 3.0 US',
    install_requires=['unicodecsv>=0.9.3'],
)
