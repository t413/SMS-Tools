import glob
from distutils.core import setup

try:
    import pypandoc
    description = pypandoc.convert("README.md", 'rst')
    print description
except:
    print "install pypandoc to get fancy .rst readme"
    description = "Universal SMS conversion tool"

setup(
    name='SMSTools',
    version='0.0.8',
    description='Universal SMS conversion tool',
    long_description=description,
    author='Tim O\'Brien',
    author_email='timo@t413.com',
    packages=['smstools', 'smstools.tests'],
    scripts=['bin/smstools'],
    url='https://github.com/t413/SMS-Tools',
    license='CC BY-NC-SA 3.0 US',
)
