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

    security.declarePrivate('_searchMemberData')
    def _searchMemberData(self, params):
        """Search members using MemberData._members.

        Does an AND search for all key, value of the params.
        If the member attributes corresponding to a key is a list,
        does an OR search on all the list elements.
        If the passed value is a string, does a substring lowercase.
        If the passed value is a list, does OR search with exact match.
        Returns a list of member ids.
        """
        _marker = []
        res = []
        inlist = {}
        searchlist = {}
        for key, value in params.items():
            if type(value) is type(''):
                inlist[key] = 0
                searchlist[key] = value.lower()
            else:
                inlist[key] = 1
                searchlist[key] = value
        mdtool = getToolByName(self, 'portal_memberdata')
        aclu = self.acl_users
        for user_wrapper in mdtool._members.values():
            # user_wrapper is a MemberData without context
            userid = user_wrapper.id
            user = _marker
            found = 1
            for key, value in searchlist.items():
                if key == self.password_field:
                    continue # ignore search on password field
                elif key == self.roles_field:
                    if user is _marker: user = aclu.getUserById(userid)
                    if user is not None:
                        searched = user.getRoles()
                    else: # unpruned user in higher user folder
                        searched = None
                elif key == self.groups_field:
                    if hasattr(aclu, 'setGroupsOfUser'):
                        if user is _marker: user = aclu.getUserById(userid)
                        if user is not None:
                            try:
                                searched = user.getGroups()
                            except AttributeError:
                                searched = None
                        else:
                            searched = None
                    else:
                        searched = None
                else:
                    searched = getattr(user_wrapper, key, None)
                if searched is None:
                    found = 0
                    break
                if type(searched) is type(''):
                    searched = (searched, )
                matched = 0
                for item in searched:
                    if inlist[key]:
                        matched = item in value
                    else:
                        matched = item.lower().find(value) != -1
                    if matched:
                        break
                if not matched:
                    found = 0
                    break
            if found:
                res.append(userid)

        return res

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
    def searchEntries(self, **kw):
        """Search for entries in the directory.
        """
        return self._searchMemberData(kw)

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
                value = NO_PASSWORD
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
                if value != NO_PASSWORD:
                    self._setMemberPassword(member, value)
            elif fieldid == dir.roles_field:
                self._setMemberRoles(member, value)
            elif fieldid == dir.groups_field:
                self._setMemberGroups(member, value)
            else:
                mapping[fieldid] = value
        if mapping:
            member.setMemberProperties(mapping)

InitializeClass(MemberStorageAdapter)
