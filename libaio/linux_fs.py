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
Minimal adaptation of linux/fs.h .
"""
__all__ = (
    'RWF_HIPRI', 'RWF_DSYNC', 'RWF_SYNC', 'RWF_NOWAIT', 'RWF_APPEND',
)

# pylint: disable=bad-whitespace
RWF_HIPRI  = 0x00000001
RWF_DSYNC  = 0x00000002
RWF_SYNC   = 0x00000004
RWF_NOWAIT = 0x00000008
RWF_APPEND = 0x00000010
# pylint: enable=bad-whitespace
