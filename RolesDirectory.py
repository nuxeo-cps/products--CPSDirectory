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
"""RolesDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = []


class RolesDirectory(BaseDirectory):
    """Roles Directory.

    A directory that represents the roles.
    """

    meta_type = 'CPS Roles Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'role_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for role'},
        {'id': 'members_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for members'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        )

    role_field = 'role'
    members_field = 'members'
    title_field = 'role'

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [RoleStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
        return adapters

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        roles = [r for r in portal.valid_roles()
                 if r not in ('Anonymous', 'Authenticated', 'Owner')]
        return roles

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        return {
            'role': id,
            'members': ('Raoul', 'XXX')
            }

InitializeClass(RolesDirectory)


class RoleStorageAdapter(BaseStorageAdapter):
    """Roles Storage Adapter

    This adapter gets and sets data from the user folder.
    """

    def __init__(self, schema, role, dir):
        """Create an Adapter for a schema.
        """
        self._role = role
        self._dir = dir
        self._portal = getToolByName(dir, 'portal_url').getPortalObject()
        BaseStorageAdapter.__init__(self, schema)

    def _getValidRoles(self):
        """Get the list of valid roles.
        """
        # XXX take into account LDAPUserFolder API to get all roles.
        return self._portal.valid_roles()

    def _getRoleMembers(self, role):
        # XXX Stupid slow search for now. Optimizable for LDAP.
        if role not in self._getValidRoles():
            raise KeyError("No role '%s'" % role)
        aclu = self._portal.acl_users
        members = []
        # XXX with LDAP getUsers returns only cached users !!! XXX
        for user in aclu.getUsers():
            if role in user.getRoles():
                members.append(user.getUserName())
        return members

    def _setRoleMembers(self, role, members):
        # XXX treat LDAP
        aclu = self._portal.acl_users
        # XXX with LDAP getUsers returns only cached users !!! XXX
        for user in aclu.getUsers():
            id = user.getUserName()
            roles = user.getRoles()
            changed = 0
            if id in members and role not in roles:
                roles = list(roles) + [role]
                changed = 1
            elif id not in members and role in roles:
                roles = list(roles)
                roles.remove(role)
                changed = 1
            if changed:
                aclu._doChangeUser(id, None, roles, user.getDomains())

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        role = self._role
        dir = self._dir
        members = self._getRoleMembers(role)
        data = {}
        for fieldid, field in self._schema.items():
            if fieldid == dir.role_field:
                value = role
            elif fieldid == dir.members_field:
                value = members
            else:
                raise ValueError("Invalid field %s for roles" % fieldid)
            data[fieldid] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        role = self._role
        dir = self._dir
        for fieldid, field in self._schema.items():
            value = data[fieldid]
            if fieldid == dir.members_field:
                self._setRoleMembers(role, value)

InitializeClass(RoleStorageAdapter)
