# Copyright (C) 2010-2016  Vincent Pelletier <plr.vincent@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
from setuptools import setup
from codecs import open
import os
import sys

extra = {}
if sys.version_info >= (3, ):
    extra['use_2to3'] = True

long_description = open(
    os.path.join(os.path.dirname(__file__), 'README.rst'),
    encoding='utf8',
).read()

setup(
    name='libaio',
    description=next(x for x in long_description.splitlines() if x.strip()),
    long_description='.. contents::\n\n' + long_description,
    keywords='linux aio libaio',
    version='0.1',
    author='Vincent Pelletier',
    author_email='plr.vincent@gmail.com',
    url='http://github.com/vpelletier/python-libaio',
    license='LGPLv3+',
    platforms=['linux'],
    packages=['libaio'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries',
    ],
    zip_safe=True,
    **extra
)
