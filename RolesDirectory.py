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
from Acquisition import aq_base
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
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [RoleStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
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

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.
        """
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        kwrole = kw.get(self.id_field)
        if kwrole:
            if isinstance(kwrole, StringType):
                if self.id_field in self.search_substring_fields:
                    kwrole = kwrole.lower()
            elif isinstance(kwrole, ListType) or isinstance(kwrole, TupleType):
                pass
            else:
                raise ValueError("Bad value for %s: %s" %
                                 (self.id_field, kwrole))
        kwmembers = kw.get(self.members_field)
        if isinstance(kwmembers, StringType):
            kwmembers = [kwmembers]
        user_roles = None # Lazily computed.
        roles = []
        for role in self.listEntryIds():
            if kwrole:
                if isinstance(kwrole, StringType):
                    if self.id_field in self.search_substring_fields:
                        if role.lower().find(kwrole) == -1:
                            continue
                    else:
                        if role != kwrole:
                            continue
                else:
                    if role not in kwrole:
                        continue
            if kwmembers:
                if user_roles is None:
                    # We'll have to search by users, build info on them.
                    # XXX Optimize this using a new getRolesWithUsers() API.
                    # XXX We cannot use getUsers because LDAPUserFolder and
                    # PluggableUserFolder return only cached users.
                    user_roles = {}
                    for username in portal.acl_users.getUserNames():
                        user = aclu.getUser(username)
                        user_roles[username] = tuple(user.getRoles())
                ok = 0
                for username in kwmembers:
                    if role in user_roles.get(username, []):
                        ok = 1
                        break
                if not ok:
                    continue
            roles.append(role)
        if not return_fields:
            return roles
        else:
            # No fields are returned even if return_fields is set.
            # This is for speed reasons, calling getEntry on each entry
            # is too slow.
            # XXX: implement optimized version.
            return [ (role, {}) for role in roles]

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
        role = entry[self.id_field]
        if self.hasEntry(role):
            raise KeyError("Role '%s' already exists" % role)
        if role in ('Anonymous', 'Authenticated', 'Owner', ''):
            raise ValueError("Role '%s' is invalid" % role)
        aclu = self.acl_users
        if hasattr(aq_base(aclu), 'userFolderAddRole'):
            aclu.userFolderAddRole(role)
        else:
            # Basic folder... add the role by hand on the portal.
            portal = getToolByName(self, 'portal_url').getPortalObject()
            portal._addRole(role)
        self.editEntry(entry)

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
        # XXX This returns more roles than the LDAP ones...
        return self._portal.valid_roles()

    def _getRoleMembers(self, role):
        if role not in self._getValidRoles():
            raise KeyError("No role '%s'" % role)
        aclu = self._portal.acl_users
        members = []
        if hasattr(aq_base(aclu), 'getLDAPSchema'):
            # LDAPUserFolder XXX
            # XXX can still be optimized if rdn is login_attr
            users = aclu.getGroupedUsers([role])
            for user in users:
                members.append(user.getUserName())
        else:
            # With LDAP or PluggableUserFolder, getUsers returns only cached
            # users, so we have to user getUserNames instead.
            # XXX Invent a better API than this SLOW search.
            for username in aclu.getUserNames():
                user = aclu.getUser(username)
                if role in user.getRoles():
                    members.append(user.getUserName())
        return members

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
                    aclu._doChangeUser(id, None, roles, user.getDomains())
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

    def _setFieldData(self, field_id, field, value):
        """Set data for one field."""
        dir = self._dir
        role = self._role
        if field_id == dir.members_field:
            self._setRoleMembers(role, value)

InitializeClass(RoleStorageAdapter)
