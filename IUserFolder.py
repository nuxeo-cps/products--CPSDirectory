# Copyright (c) 2004 Nuxeo SARL <http://nuxeo.com>
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

"""This file defines the interface required by CPSDirectories for UserFolders,
Users and Groups.
"""

__doc__ = '''User Folder Interfaces'''
__version__ = '$Revision$'[11:-2]

import Interface

class IUserFolder(Interface.Base):
    # Part of the standard acl_users API:
    def getUserNames(self):
        """Return a list of usernames"""

    def getUser(self, name):
        """Return the named user object or None"""

    def _doChangeUser(self, name, password, roles, domains, **kw):
        """Modify an existing user. This should be implemented by subclasses
           to make the actual changes to a user. The 'password' will be the
           original input password, unencrypted. The implementation of this
           method is responsible for performing any needed encryption."""

    # Group support
    def setGroupsOfUser(self, groupnames, username):
        """Set the groups of a user"""

    def setUsersOfGroup(self, usernames, groupname):
        """Set the users of the group"""

    def getGroupNames(self):
        """Return a list of group names"""

    def getGroupById(self, groupname):
        """Return the given group"""

    def userFolderAddGroup(self, groupname, **kw):
        """Create a group"""

    # Only on LDAPUserFolders
    def manage_editUserPassword(self, dn, new_pw, REQUEST=None):
        """ Change a user password """

    def manage_editUserGroups(self, user_dn, usergroup_dns=[], REQUEST=None):
        """ Edit the user groups of a user """

    def userFolderAddRole(self, role):
        """Add a new role."""

    def getGroupedUsers(self, groups=None):
        """ Return all those users that are in a group """


class IUser(Interface.Base):
    # Part of the standard user API:
    def getRoles(self):
        """Return the list of roles assigned to a user."""

    def getUserName(self):
        """Return the username of a user"""

    def getId(self):
        """Get the ID of the user. The ID can be used, at least from
        Python, to get the user from the user's
        UserDatabase"""
        # Today this, and getId() is the same. It is my uderstanding that
        # getUserName() is preferred. There is for example no getUserIds()

    def getRoles(self):
        """Return the list of roles assigned to a user."""

    def getDomains(self):
        """Return the list of domain restrictions for a user"""

    # Group support:
    def getGroupNames(self):
        """Return a list of group names"""

    # Only on LDAPUsers:
    def getUserDN(self):
        """ Return the user's full Distinguished Name """


class IGroup(Interface.Base):
    # On pluggableUserFolder:
    def getMembers(self):
        """Returns the members of the group

        Does not return users who are members of memeber groups.
        """

    def getGroups(self):
        """Returns the groups who are a member of the group"""

    def setGroups(self, groupids):
        """Sets the groups that are members of the group"""

    # On non-PluggableUserFolders
    def getUsers(self):
        """Returns the users that are a members of the groups"""

