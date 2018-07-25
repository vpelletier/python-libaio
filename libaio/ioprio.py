# Copyright (C) 2018  Vincent Pelletier <plr.vincent@gmail.com>
#
# This file is part of python-libaio.
# python-libaio is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# python-libaio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with python-libaio.  If not, see <http://www.gnu.org/licenses/>.
"""
Minimal adaptation of ioprio.h .
"""
__all__ = (
    'IOPRIO_PRIO_VALUE',
    'IOPRIO_CLASS_RT', 'IOPRIO_CLASS_BE', 'IOPRIO_CLASS_IDLE',
)
IOPRIO_CLASS_SHIFT = 13
IOPRIO_PRIO_VALUE = lambda klass, data: (klass << IOPRIO_CLASS_SHIFT) | data

IOPRIO_CLASS_RT = 1
IOPRIO_CLASS_BE = 2
IOPRIO_CLASS_IDLE = 3
