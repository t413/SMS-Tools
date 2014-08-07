import glob
from distutils.core import setup


# get all of the scripts
scripts = glob.glob("core/*")

setup(
    name='SMSTools',
    version='0.0.8',
    description='Universal SMS conversion tool',
    author='Tim O\'Brien',
    author_email='timo@t413.com',
    packages=['smstools', 'smstools.test'],
    scripts=scripts,
    url='https://github.com/t413/SMS-Tools',
    license='CC BY-NC-SA 3.0 US',
)
