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
"""GroupsDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = []


class GroupsDirectory(BaseDirectory):
    """Groups Directory.

    A directory that represents the groups.
    """

    meta_type = 'CPS Groups Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'group_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for group'},
        {'id': 'users_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for users'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        )

    group_field = 'group'
    users_field = 'users'
    title_field = 'group'

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [GroupStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
        return adapters

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        return {
            'group': id,
            'users': ('Bobby', 'XXX')
            }

InitializeClass(GroupsDirectory)


class GroupStorageAdapter(BaseStorageAdapter):
    """Groups Storage Adapter

    This adapter gets and sets data from the user folder.
    """

    def __init__(self, schema, group, dir):
        """Create an Adapter for a schema.
        """
        self._group = group
        self._dir = dir
        self._portal = getToolByName(dir, 'portal_url').getPortalObject()
        BaseStorageAdapter.__init__(self, schema)

    def _delete(self, field_id):
        raise NotImplementedError

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        group = self._group
        dir = self._dir
        aclu = self._portal.acl_users
        if hasattr(aclu, 'getGroupById'):
            groupob = aclu.getGroupById(group, _marker)
            if groupob is _marker:
                raise KeyError("No group '%s'" % group)
            users = groupob.getUsers()
        # else try other APIs to get to group.
        else:
            users = ()
        data = {}
        for fieldid, field in self._schema.items():
            if fieldid == dir.group_field:
                value = group
            elif fieldid == dir.users_field:
                value = users
            else:
                raise ValueError("Invalid field %s for groups" % fieldid)
            data[fieldid] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        raise NotImplementedError

InitializeClass(GroupStorageAdapter)
