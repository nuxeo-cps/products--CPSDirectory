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

from zLOG import LOG, DEBUG, WARNING

from Globals import InitializeClass
from Acquisition import aq_base
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
        {'id': 'subgroups_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for sub groups'},
        )

    id_field = 'group'
    title_field = 'group'
    members_field = 'members'
    subgroups_field = 'subgroups'

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

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        kwgroup = kw.get(self.id_field)
        kwmembers = kw.get(self.members_field)
        groups = []
        for group in self.listEntryIds():
            if kwgroup:
                # XXX treat list
                if group != kwgroup:
                    continue
            if kwmembers:
                if not hasattr(aq_base(aclu), 'getGroupById'):
                    # No group support and want a member
                    continue
                # XXX optimize for LDAP, using a getGroupsWithUsers()
                ok = 0
                groupob = aclu.getGroupById(group, _marker)
                if groupob is _marker:
                    raise KeyError("No group '%s'" % group)
                for userid in groupob.getUsers():
                    if userid in kwmembers:
                        ok = 1
                        break
                if not ok:
                    continue
            groups.append(group)
        if return_fields is None:
            return groups
        else:
            return [(g, {}) for g in groups]

        res = []
        for group in groups:
            entry = self.getEntry(group)
            ret_data = {}
            for key in return_fields:
                ret_data[key] = entry[key]
            res.append((group, ret_data))
        return res

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        # XXX check security?
        # XXX optimize for LDAP
        return id in self.listEntryIds()

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed()
        group = entry[self.id_field]
        if self.hasEntry(group):
            raise ValueError("Group '%s' already exists" % group)
        aclu = self.acl_users
        if not hasattr(aq_base(aclu), 'userFolderAddGroup'):
            return # XXX
        aclu.userFolderAddGroup(group)
        self.editEntry(entry)

    security.declarePublic('hasSubGroupsSupport')
    def hasSubGroupsSupport(self):
        """Tells if the current acl_users has subgroups support.
        """
        aclu = self.acl_users
        supported_aclus = ('Pluggable User Folder',)
        if aclu.meta_type in supported_aclus:
            return 1
        return 0

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
            if aclu.meta_type == 'Pluggable User Folder':
                return groupob.getMembers()
            else:
                return tuple(groupob.getUsers())
        # else try other APIs to get to group.
        return ()

    def _setGroupMembers(self, group, members):
        aclu = self._portal.acl_users
        if hasattr(aq_base(aclu), 'setUsersOfGroup'):
            aclu.setUsersOfGroup(members, group)
        # else try other APIs to get to group.

    def _getGroupSubGroups(self, group):
        """Returns the subgroups of the named group"""
        aclu = self._portal.acl_users
        if not hasattr(aq_base(aclu), 'getGroupById'):
            return ()
        groupob = aclu.getGroupById(group)
        if hasattr(aq_base(groupob), 'getGroups'): # PluggableUserFolder
            return groupob.getGroups()
        return ()

    def _setGroupSubGroups(self, group, subgroups):
        """Set the subgroups of the named group"""
        aclu = self._portal.acl_users
        groupob = aclu.getGroupById(group)
        if hasattr(aq_base(groupob), 'setGroups'): # PluggableUserFolder
            groupob.setGroups(subgroups)
            return
        LOG('GroupsDirectory', WARNING,
            'Attempt to set groups on groups on unsupported User Folder')
        return None

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        group = self._group
        if group is None:
            # Creation.
            return self.getDefaultData()
        return self._getData()

    def _getFieldData(self, field_id, field):
        """Get data from one field."""
        dir = self._dir
        group = self._group
        if field_id == dir.id_field:
            value = group
        elif field_id == dir.members_field:
            value = self._getGroupMembers(group)
        elif field_id == dir.subgroups_field:
            value = self._getGroupSubGroups(group)
        else:
            raise ValueError("Invalid field %s for groups" % field_id)
        return value

    def _setFieldData(self, field_id, field, value):
        """Set data for one field."""
        dir = self._dir
        group = self._group
        if field_id == dir.members_field:
            self._setGroupMembers(group, value)
        elif field_id == dir.subgroups_field:
            self._setGroupSubGroups(group, value)

InitializeClass(GroupStorageAdapter)
