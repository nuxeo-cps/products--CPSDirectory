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

from zLOG import LOG, DEBUG, WARNING

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = []

NO_PASSWORD = '__NO_PASSWORD__'


class MembersDirectory(BaseDirectory):
    """Members Directory.

    A directory that know how to deal with members.

    In the role ACLs for the fields of this directory, the role "Owner"
    is set when you edit your own entry.
    """

    meta_type = 'CPS Members Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for password'},
        {'id': 'roles_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for roles'},
        {'id': 'groups_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for groups'},
        )

    id_field = 'id'
    title_field = 'id'
    password_field = 'password'
    roles_field = 'roles'
    groups_field = 'groups'

    # Provide more useful defaults for this directory.
    acl_entry_edit_roles = 'Manager; Owner'
    acl_entry_edit_roles_c = ['Manager', 'Owner']

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

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        aclu = portal.acl_users
        ids = list(aclu.getUserNames())
        ids.sort()
        return ids
        # Note: LDAPUserFolder's getUsers only returns cached users,
        # and the following would call it so isn't correct.
        #ids = getToolByName(dir, 'portal_membership').listMemberIds()

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        mdtool = getToolByName(self, 'portal_memberdata')
        # Convert special fields id/roles/groups to known names.
        for f, p in ((self.id_field, 'id'),
                     (self.roles_field, 'roles'),
                     (self.groups_field, 'groups')):
            if f != p and kw.has_key(f):
                kw[p] = kw[f]
                del kw[f]
            # XXX should also convert search_substring_fields
        res = mdtool.searchForMembers(kw, props=return_fields,
                                      options={'search_substring_props':
                                               self.search_substring_fields,
                                               })
        # XXX if returning props, back-convert known names.
        return res

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        # XXX check security?
        aclu = self.acl_users
        return id in aclu.getUserNames()

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.

        XXX: OK, but what exactly is an 'entry'?
        """
        self.checkCreateEntryAllowed()
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise KeyError("Member '%s' already exists" % id)
        mtool = getToolByName(self, 'portal_membership')
        password = '38fnvas7ds' # XXX default password ???
        roles = ()
        domains = []
        mtool.addMember(id, password, roles, domains)
        member = mtool.getMemberById(id)
        if member is None or not hasattr(aq_base(member), 'getMemberId'):
            raise ValueError("Cannot add member '%s'" % id)
        member.setMemberProperties({}) # Trigger registration in memberdata.
        self.editEntry(entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed()
        if not self.hasEntry(id):
            raise KeyError("Members '%s' does not exist" % id)
        aclu = self.acl_users
        aclu._doDelUsers([id])

InitializeClass(MembersDirectory)


class MemberStorageAdapter(BaseStorageAdapter):
    """Members Storage Adapter

    This adapter gets and sets data from the user folder and the member
    data.
    """

    def __init__(self, schema, id, dir):
        """Create an Adapter for a schema.

        The id passed is the member id. It may be None for creation.
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
        aclu = self._dir.acl_users
        user = member.getUser()
        if hasattr(aq_base(aclu), 'manage_editUserPassword'):
            # LDAPUserFolder XXX
            if hasattr(aq_base(user), 'getUserDN'):
                user_dn = user.getUserDN()
                aclu.manage_editUserPassword(user_dn, password)
            else:
                LOG('_setMemberPassword', DEBUG, 'member %s is not in LDAP'
                    % member)
        else:
            aclu._doChangeUser(user.getUserName(), password,
                               user.getRoles(), user.getDomains())

    def _getMemberRoles(self, member):
        roles = member.getUser().getRoles()
        return [r for r in roles
                if r not in ('Anonymous', 'Authenticated', 'Owner')]

    def _setMemberRoles(self, member, roles):
        aclu = self._dir.acl_users
        user = member.getUser()
        if hasattr(aq_base(aclu), 'manage_editUserRoles'):
            # LDAPUserFolder XXX
            if hasattr(aq_base(user), 'getUserDN'):
                user_dn = user.getUserDN()
                aclu.manage_editUserRoles(user_dn, list(roles))
            else:
                LOG('_setMemberRoles', DEBUG, 'member %s is not in LDAP'
                    % member)
        else:
            aclu._doChangeUser(user.getUserName(), None,
                               list(roles), user.getDomains())

    def _getMemberGroups(self, member):
        user = member.getUser()
        if hasattr(aq_base(user), 'getGroups'):
            return user.getGroups()
        else:
            return () # XXX or field.getDefault() ?

    def _setMemberGroups(self, member, groups):
        LOG('_setMemberGroups', DEBUG, 'set member=%s groups=%s' %
            (member, groups))
        aclu = self._dir.acl_users # XXX
        user = member.getUser()
        if hasattr(aq_base(aclu), 'manage_editUserGroups'):
            # LDAPUserFolder XXX
            if hasattr(aq_base(user), 'getUserDN'):
                user_dn = user.getUserDN()
                aclu.manage_editUserGroups(user_dn, list(groups))
            else:
                LOG('_setMemberGroups', DEBUG, 'member %s is not in LDAP'
                    % member)
        elif hasattr(aq_base(aclu), 'setGroupsOfUser'):
            aclu.setGroupsOfUser(list(groups), user.getUserName())
        else:
            LOG('_setMemberGroups', WARNING, 'No group support found in UserFolder')


    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        if id is None:
            # Creation.
            return self.getDefaultData()
        # Pass member as kw to _getFieldData.
        return self._getData(member=self._getMember())

    def _getFieldData(self, field_id, field, member=None):
        """Get data from one field."""
        dir = self._dir
        if field_id == dir.id_field:
            value = self._id
        elif field_id == dir.password_field:
            value = NO_PASSWORD
        elif field_id == dir.roles_field:
            value = self._getMemberRoles(member)
        elif field_id == dir.groups_field:
            value = self._getMemberGroups(member)
        else:
            value = member.getProperty(field_id, _marker)
            if value is _marker:
                value = field.getDefault()
        return value

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)

        dir = self._dir
        member = self._getMember()
        mapping = {}
        for field_id, value in data.items():
            if field_id == dir.id_field:
                pass
                #raise ValueError("Can't write to id") # XXX
            elif field_id == dir.password_field:
                if value != NO_PASSWORD:
                    self._setMemberPassword(member, value)
            elif field_id == dir.roles_field:
                self._setMemberRoles(member, value)
            elif field_id == dir.groups_field:
                self._setMemberGroups(member, value)
            else:
                mapping[field_id] = value
        if mapping:
            member.setMemberProperties(mapping)

InitializeClass(MemberStorageAdapter)
