# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
"""BaseDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import SimpleItemWithProperties


class BaseDirectory(SimpleItemWithProperties):
    """Base Directory.

    A directory holds information about entries and how to access and
    display them.
    """

    meta_type = None

    security = ClassSecurityInfo()

    _properties = SimpleItemWithProperties._properties + (
        {'id': 'schema', 'type': 'string', 'mode': 'w',
         'label': 'Schema'},
        )

    schema = ''

    def __init__(self, id, **kw):
        self.id = id

InitializeClass(BaseDirectory)
