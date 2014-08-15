import os, json
from distutils.core import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

v = json.loads(read("VERSION"))
__version__ = "%i.%i.%i" % (v['version_major'],v['version_minor'],v['version_patch'])

setup(
    name='smstools',
    version=__version__,
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
