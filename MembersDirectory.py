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
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = []


class MembersDirectory(BaseDirectory):
    """Members Directory.

    A directory that know how to deal with members.
    """

    meta_type = 'CPS Members Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'id_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for id'},
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for password'},
        {'id': 'roles_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for roles'},
        {'id': 'groups_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for groups'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        )

    id_field = 'id'
    password_field = 'password'
    roles_field = 'roles'
    groups_field = 'groups'
    title_field = 'id'

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [MemberStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
        return adapters

    security.declarePrivate('_getAdditionalRoles')
    def _getAdditionalRoles(self, id):
        """Get additional user roles provided to ACLs."""
        if id == getSecurityManager().getUser().getId():
            return ('Owner',)
        else:
            return ()

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        # Note: LDAPUserFolder's getUsers only returns cached users.
        return tuple(aclu.getUserNames())

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

    def _getMember(self):
        member = self._mtool.getMemberById(self._id)
        if member is None:
            raise KeyError("No member '%s'" % self._id)
        if not hasattr(aq_base(member), 'getMemberId'):
            raise KeyError("User '%s' is not a member" % self._id)
        return member

    def _setMemberPassword(self, member, password):
        aclu = self._dir.acl_users # XXX
        if hasattr(aq_base(aclu), 'manage_editUserPassword'):
            # LDAPUserFolder
            # XXX find dn
            raise NotImplementedError
            dn = None
            aclu.manage_editUserPassword(dn, password)
        else:
            user = member.getUser()
            aclu._doChangeUser(user.getUserName(), password,
                               user.getRoles(), user.getDomains())

    def _getMemberRoles(self, member):
        roles = member.getUser().getRoles()
        return [r for r in roles
                if r not in ('Anonymous', 'Authenticated', 'Owner')]

    def _setMemberRoles(self, member, roles):
        aclu = self._dir.acl_users # XXX
        if hasattr(aq_base(aclu), 'manage_editUserRoles'):
            # LDAPUserFolder
            # XXX find dn
            raise NotImplementedError
            aclu.manage_editUserRoles(dn, role_dns)
        else:
            user = member.getUser()
            aclu._doChangeUser(user.getUserName(), None,
                               list(roles), user.getDomains())

    def _getMemberGroups(self, member):
        user = member.getUser()
        if hasattr(aq_base(user), 'getGroups'):
            return user.getGroups()
        else:
            return () # XXX or field.getDefault() ?

    def _setMemberGroups(self, member, groups):
        aclu = self._dir.acl_users # XXX
        if hasattr(aq_base(aclu), 'manage_editUserGroupsXXXXXX'):
            # LDAPUserFolder
            # XXX find dn
            raise NotImplementedError
        else:
            user = member.getUser()
            if hasattr(aq_base(user), 'setGroupsOfUser'):
                aclu.setGroupsOfUser(list(groups), user.getUserName())

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        dir = self._dir
        member = self._getMember()
        data = {}
        for fieldid, field in self._schema.items():
            if fieldid == dir.id_field:
                value = id
            elif fieldid == dir.password_field:
                value = 'this is the password XXX'
            elif fieldid == dir.roles_field:
                value = self._getMemberRoles(member)
            elif fieldid == dir.groups_field:
                value = self._getMemberGroups(member)
            else:
                value = member.getProperty(fieldid, _marker)
                if value is _marker:
                    value = field.getDefault()
            data[fieldid] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        dir = self._dir
        member = self._getMember()
        mapping = {}
        for fieldid, field in self._schema.items():
            value = data[fieldid]
            if fieldid == dir.id_field:
                pass
                #raise ValueError("Can't write to id") # XXX
            elif fieldid == dir.password_field:
                if value:
                    self._setMemberPassword(member, value)
                else:
                    raise ValueError("Can't write empty password") # XXX
            elif fieldid == dir.roles_field:
                self._setMemberRoles(member, value)
            elif fieldid == dir.groups_field:
                self._setMemberGroups(member, value)
            else:
                mapping[fieldid] = value
        if mapping:
            member.setMemberProperties(mapping)

InitializeClass(MemberStorageAdapter)
