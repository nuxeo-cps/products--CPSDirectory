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

"""This module defines the interfaces required by CPSDirectories for
UserFolders, Users and Groups.
"""

__version__ = '$Revision$'[11:-2]

import Interface

class IUserFolder(Interface.Base):
    #
    # BasicUserFolder API
    #
    # These are part of the BasicUserFolder API, but are not implemented
    # in BasicUserFolder, and will therefore need overriding, either by
    # subclassing from UserFolder instead of BasicUserFolder, or by
    # implementing them in the user folder itself.
    #
    # They are not CPS specific, but listed for completeness as CPS calls them.
    def getUserNames():
        """Return a list of usernames"""

    def getUser(name):
        """Return the named user object or None"""

    def userFolderAddUser(name, password, roles, domains, **kw):
        """API method for creating a new user object. Note that not all
           user folder implementations support dynamic creation of user
           objects."""

    #
    # CPS Role management extensions
    #
    # These are not called directly. Instead they are called
    # via CPSCore.utils. The methods there will check if
    # acl_users implement these methods and call it. If not,
    # a default version is called that assumes a standard user folder
    # without group support.
    def mergedLocalRoles(object, withgroups=0):
        """
        Return a merging of object and its ancestors' __ac_local_roles__.
        When called with withgroups=1, the keys are
        of the form user:foo and group:bar.
        """

    def mergedLocalRolesWithPath(object, withgroups=0):
        """
        Return a merging of object and its ancestors' __ac_local_roles__.
        When called with withgroups=1, the keys are
        of the form user:foo and group:bar.
        The path corresponding
        to the object where the role takes place is added
        with the role in the result. In this case of the form :
        {'user:foo': [{'url':url, 'roles':[Role0, Role1]},
                    {'url':url, 'roles':[Role1]}],..}.
        """

    # There are default versions of thes following methods patched into
    # BasicUserFolder. These are not necessarily very efficient
    # and user folders may want to override them, especially in
    # the case of external storage, such as LDAP.
    def setRolesOfUser(roles, username):
        """Sets the users of a role"""

    def setUsersOfRole(usernames, role):
        """Sets the users of a role"""

    def getUsersOfRole(role):
        """Gets the users of a role"""

    def userFolderAddRole(role):
        """Add a new role."""

    def userFolderDelRoles(rolenames):
        """Delete roles."""

    #
    # CPS Group support
    #
    # A CPS UserFolder should have some kind of group support.
    # These methods are needed to support this.
    def setGroupsOfUser(groupnames, username):
        """Set the groups of a user"""

    def setUsersOfGroup(usernames, groupname):
        """Set the users of the group"""

    def getGroupNames():
        """Return a list of group names"""

    def getGroupById(groupname):
        """Return the given group"""

    def userFolderAddGroup(groupname, **kw):
        """Create a group"""

    def userFolderDelGroups(groupnames):
        """Delete groups"""
    
    
    #
    # Extended search API
    #
    # To support efficient searches of external user sources,
    # An extended search API is defined. A default version of this
    # is patched into BasicUserFolder, but that will give horrible
    # results on extended sources. Also, it supports no extended
    # attributes, which is common on external sources.
    def listUserProperties():
        """Lists properties settable or searchable on the users."""

    def searchUsers(query={}, props=None, options=None, **kw):
        """Search for users having certain properties.

        If props is None, returns a list of ids:
        ['user1', 'user2']

        If props is not None, it must be sequence of property ids. The
        method will return a list of tuples containing the user id and a
        dictionary of available properties:
        [('user1', {'email': 'foo', 'age': 75}), ('user2', {'age': 5})]

        Options is used to specify the search type if possible. XXX

        Special properties are 'id', 'roles', 'groups'.
        """


class IUser(Interface.Base):
    #
    # Part of the standard user API:
    #
    # These must be implemented as a patr of ANY user object, not just
    # for CPS. They are listed here to make the list complete.
    def getRoles():
        """Return the list of roles assigned to a user."""

    def getUserName():
        """Return the username of a user"""

    def getId():
        """Get the ID of the user. The ID can be used, at least from
        Python, to get the user from the user's
        UserDatabase"""
        # The difference between getID and getUserName is that the ID is 
        # the ID used when storing the user, while the username is what
        # the user types in the login box. This is the same in 99% of 
        # cases (even with LDAP they are the same, and getUserDN is used
        # to get the storage ID). Most likely the usage throughout CMF, 
        # and probably also CPS is inconsistent. Fixing this is a low
        # priority, since all the userfodlers we support now does not
        # differ between id and username.

    def getDomains():
        """Return the list of domain restrictions for a user"""

    #
    # CPS Group support:
    #
    def getGroups():
        """Return the names of the groups that the user is a member of"""

    def getComputedGroups():
        """Return the names of the groups that the user is a member of

        This also returns the groups which the grups are members of.
        This method is not required by CPS, and only used if the userfolder
        has groups in groups support."""

    #
    # CPS Property support:
    #
    def listProperties():
        """Lists all properties that are set on the user."""

    def hasProperty(id):
        """Check for a property"""

    def getProperty(id, default=None):
        """Returns the value of a property"""

    def getProperties(ids):
        """Returns the values of list of properties"""
        # Returns as a dictionary, I hope?

    def setProperty(id, value):
        """Sets the value of a property"""

    def setProperties(**kw):
        """Sets the values of a dictionary of properties"""


class IGroup(Interface.Base):
    def getUsers():
        """Returns the members of the group

        Does not return users who are members of member groups.
        Use this when you want to LIST the users of a group, for example
        in a management interface.
        """

    def getComputedUsers():
        """Returns the users that are a members of the groups

        Returns members of subgroups as well as the main group.
        Use this when you want to find all users that are affected by
        the groups roles, so called by the access control methods.
        """

    #
    # Subgroup support.
    #
    # Having groups in groups is supported, but optional in CPS.
    def getGroups():
        """Returns the groups who are a member of the group"""

    def setGroups(groupids):
        """Sets the groups that are members of the group"""

