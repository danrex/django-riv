from distutils.core import setup
from setuptools import find_packages

setup(
    name='django-riv',
    version='0.1.0',
    description='A djangoish REST framework',
    author='Christian Graf',
    author_email='email.christiangraf.de',
    url='http://github.com/danrex/django-riv',
    packages=find_packages(),
    license='LICENSE',
    long_description=open('README.md').read(),
    zip_safe=False,
    install_requires=[
        'Django >= 1.2',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
    ],
)
