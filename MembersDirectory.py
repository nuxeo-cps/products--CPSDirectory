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
"""MembersDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


class MembersDirectory(BaseDirectory):
    """Members Directory.

    A directory that know how to deal with members.
    """

    meta_type = 'CPS Members Directory'

    security = ClassSecurityInfo()

    security.declarePrivate('getAdapters')
    def getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [MemberStorageAdapter(schema, id, dir)
                    for schema in self.getSchemas()]
        return adapters

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        return {
            'id': id,
            'givenName': 'Raoul',
            'sn': id.upper(),
            }

InitializeClass(MembersDirectory)


class MemberStorageAdapter(BaseStorageAdapter):
    """Members Storage Adapter

    This adapter gets and sets data from the user folder and the member
    data.
    """

    def __init__(self, schema, id, dir):
        """Create an Adapter for a schema.

        The id passed is the member id.
        """
        self._id = id
        self._dir = dir
        self._mtool = getToolByName(dir, 'portal_membership')
        BaseStorageAdapter.__init__(self, schema)

    def _delete(self, field_id):
        raise NotImplementedError

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        data = {'id': id}
        data.update({
            'password': 'this should be invisible',
            'email': 'fg@nuxeo.com',
            })
        return data
        # XXX
        for field_id, field in self._schema.items():
            if hasattr(base_ob, field_id):
                value = getattr(ob, field_id)
            else:
                # Use default from field.
                value = field.getDefault()
            data[field_id] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        raise NotImplementedError
        for field_id in self._schema.keys():
            setattr(self._ob, field_id, data[field_id])

InitializeClass(MemberStorageAdapter)
