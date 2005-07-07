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

from types import ListType, TupleType, StringType
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


class RolesDirectory(BaseDirectory):
    """Roles Directory.

    A directory that represents the roles.
    """

    meta_type = 'CPS Roles Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'members_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for members'},
        )

    id_field = 'role'
    title_field = 'role'
    members_field = 'members'

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        dir = self
        adapters = [RoleStorageAdapter(schema, id, dir, **kw)
                    for schema in self._getSchemas(search=search)]
        return adapters

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        roles = [r for r in portal.valid_roles()
                 if r not in ('Anonymous', 'Authenticated', 'Owner')]
        return roles

    # XXX AT: overriden method, will be unnecesary when _searchEntries returns
    # dependant field values correctly
    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        title_field = self.title_field
        if self.id_field == title_field:
            res = [(id, id) for id in self.listEntryIds()]
        else:
            res = [(id, self.getEntry(id, default={}).get(self.title_field))
                   for id in self.listEntryIds()]
        return res

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        A role or list of roles to search for can be specified using the id
        field as a parameter.

        A member or list of members to search for can be specified using the
        members field as a parameter.

        If return_fields is None, return a list of role ids:
          ['role1', 'role2']

        If return_fields is not None, it must a sequence of property ids. The
        method will return a list of tuples containing the role id and a
        dictionary of available properties:
          [('role1', {'id': 'role1', 'members': ('user1', 'user2')},)]

        return_fields=['*'] means to return all available properties.
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        # roles searched for
        kwrole = kw.get(self.id_field)
        if kwrole is not None:
            if isinstance(kwrole, StringType):
                if self.id_field in self.search_substring_fields:
                    kwrole = kwrole.lower()
            elif isinstance(kwrole, ListType) or isinstance(kwrole, TupleType):
                pass
            else:
                raise ValueError("Bad value for %s: %s" %
                                 (self.id_field, kwrole))
        # members searched for
        kwmembers = kw.get(self.members_field)
        if kwmembers is not None:
            if isinstance(kwmembers, StringType):
                kwmembers = [kwmembers]
            elif isinstance(kwmembers, ListType) or\
                 isinstance(kwmembers, TupleType):
                pass
            else:
                raise ValueError("Bad value for %s: %s" %
                                 (self.members_field, kwmembers))
            user_roles = []
            # construct a list of roles covered by requested members
            for username in kwmembers:
                u = aclu.getUser(username)
                if not u:
                    continue
                for role in u.getRoles():
                    if role not in user_roles:
                        user_roles.append(role)

        # fields asked for
        if return_fields is not None:
            if isinstance(return_fields, StringType):
                return_fields = [return_fields]
            if return_fields == ['*']:
                return_fields = (self.id_field, self.title_field,
                                 self.members_field)

        LOG('RolesDirectory.searchEntries', DEBUG,
            "kwrole=%s, kwmembers=%s, return_fields=%s" %
            (str(kwrole), str(kwmembers), str(return_fields)))

        roles = []
        for role in self.listEntryIds():
            # search for a subset of roles
            if kwrole is not None:
                if isinstance(kwrole, StringType):
                    if self.id_field in self.search_substring_fields:
                        if kwrole != '*' and \
                               role.lower().find(kwrole) == -1:
                            continue
                    else:
                        if role != kwrole:
                            continue
                else:
                    if role not in kwrole:
                        continue
            # at least one of the requested users has this role
            if kwmembers is not None and role not in user_roles:
                continue
            roles.append(role)
        if not return_fields:
            return roles
        else:
            # return asked properties if available in the roles directory.
            roles_detail = []
            for role in roles:
                details = {}
                entry = self.getEntry(role)
                if self.id_field in return_fields:
                    details[self.id_field] = entry[self.id_field]
                if self.title_field in return_fields:
                    details[self.title_field] = entry[self.title_field]
                if self.members_field in return_fields:
                    members = entry[self.members_field]
                    if kwmembers is not None:
                        members = [m for m in members if m in kwmembers]
                    details[self.members_field] = tuple(members)
                roles_detail.append((role, details))
            return roles_detail

    security.declarePrivate('_hasEntry')
    def _hasEntry(self, id):
        """Does the directory have a given entry?"""
        # XXX should use base class implementation
        return id in self.listEntryIds()

    security.declarePrivate('_createEntry')
    def _createEntry(self, entry):
        """Create an entry in the directory."""
        role = entry[self.id_field]
        if self._hasEntry(role):
            raise KeyError("Role '%s' already exists" % role)
        if role in ('Anonymous', 'Authenticated', 'Owner', ''):
            raise KeyError("Role '%s' is invalid" % role)
        aclu = self.acl_users
        aclu.userFolderAddRole(role)
        self.editEntry(entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory.
        """
        self.checkDeleteEntryAllowed(id=id)
        aclu = self.acl_users
        aclu.userFolderDelRoles( (id,))

InitializeClass(RolesDirectory)


class RoleStorageAdapter(BaseStorageAdapter):
    """Roles Storage Adapter

    This adapter gets and sets data from the user folder.
    """

    def __init__(self, schema, role, dir, **kw):
        """Create an Adapter for a schema.
        """
        self._role = role
        self._dir = dir
        self._portal = getToolByName(dir, 'portal_url').getPortalObject()
        BaseStorageAdapter.__init__(self, schema, **kw)

    def _getValidRoles(self):
        """Get the list of valid roles.
        """
        # XXX take into account LDAPUserFolder API to get all roles.
        # XXX This returns more roles than the LDAP ones...
        return self._portal.valid_roles()

    def _getRoleMembers(self, role):
        if role not in self._getValidRoles():
            raise KeyError("No role '%s'" % role)
        aclu = self._portal.acl_users
        return aclu.getUsersOfRole(role)

    def _setRoleMembers(self, role, members):
        # XXX treat LDAP
        aclu = self._portal.acl_users
        # XXX See above about getUsers vs. getUserNames.
        for id in aclu.getUserNames():
            user = aclu.getUser(id)
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
                try:
                    aclu.userFolderEditUser(id, None, roles, user.getDomains())
                except KeyError:
                    # XXX PluggableUserFolder trying to change non-default
                    LOG('_setRoleMembers', DEBUG, 'Attempted to change user '
                        '%s but failed' % id)
                    raise

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        role = self._role
        if role is None:
            # Creation.
            return self.getDefaultData()
        return self._getData()

    def _getFieldData(self, field_id, field):
        """Get data from one field."""
        dir = self._dir
        role = self._role
        if field_id == dir.id_field:
            value = role
        elif field_id == dir.members_field:
            value = self._getRoleMembers(role)
        else:
            raise ValueError("Invalid field %s for roles" % field_id)
        return value

    def _setFieldData(self, field_id, value):
        """Set data for one field."""
        dir = self._dir
        role = self._role
        if field_id == dir.members_field:
            self._setRoleMembers(role, value)

InitializeClass(RoleStorageAdapter)
