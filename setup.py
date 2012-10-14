# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~~~~~

    :copyright: (c) 2010 by Dan Jacob.
    :license: BSD, see LICENSE for more details.
"""

"""
newsmeme
--------

"""
from setuptools import setup

setup(
    name='newsmeme',
    version='0.1',
    url='<enter URL here>',
    license='BSD',
    author='Dan Jacob',
    author_email='your-email-here@example.com',
    description='<enter short description here>',
    long_description=__doc__,
    packages=['newsmeme'],
    zip_safe=False,
    platforms='any',
    install_requires=[    
        # 0.9
        'Flask==0.9',
        'Flask-Cache==0.6.0',
        'Flask-SQLAlchemy==0.16',
        'Flask-Principal==0.3.1',
        'Flask-WTF==0.8',
        # 0.6.1
        'Flask-Mail == 0.6.1',
        'Flask-Testing',
        # 0.3.3
        'Flask-Script==0.3.3',
        'Flask-OpenID==1.0.1',
        'Flask-Babel==0.8',
        'Flask-Themes',
        'sqlalchemy == 0.7.8',
        'markdown == 2.2.0',
        'feedparser == 5.1.2',
        'blinker == 1.2',
        'nose== 1.1.2',
        'Flask-DebugToolbar==0.7.1',        
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
