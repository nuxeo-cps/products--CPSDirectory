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
        {'id': 'members_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for members'},
        )

    id_field = 'group'
    title_field = 'group'
    members_field = 'members'

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [GroupStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
        return adapters

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        if hasattr(aclu, 'getGroupNames'):
            return tuple(aclu.getGroupNames())
        else:
            return ()

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

    def _getGroupMembers(self, group):
        aclu = self._portal.acl_users
        if hasattr(aq_base(aclu), 'getGroupById'):
            groupob = aclu.getGroupById(group, _marker)
            if groupob is _marker:
                raise KeyError("No group '%s'" % group)
            return tuple(groupob.getUsers())
        # else try other APIs to get to group.
        return ()

    def _setGroupMembers(self, group, members):
        aclu = self._portal.acl_users
        if hasattr(aq_base(aclu), 'setUsersOfGroup'):
            aclu.setUsersOfGroup(members, group)
        # else try other APIs to get to group.

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        group = self._group
        dir = self._dir
        members = self._getGroupMembers(group)
        data = {}
        for fieldid, field in self._schema.items():
            if fieldid == dir.id_field:
                value = group
            elif fieldid == dir.members_field:
                value = members
            else:
                raise ValueError("Invalid field %s for groups" % fieldid)
            data[fieldid] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        group = self._group
        dir = self._dir
        for fieldid, field in self._schema.items():
            value = data[fieldid]
            if fieldid == dir.members_field:
                self._setGroupMembers(group, value)

InitializeClass(GroupStorageAdapter)
