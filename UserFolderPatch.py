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
"""UserFolderPatch

Patches User Folder to give it a standard API.
"""

from zLOG import LOG, TRACE

from types import StringType

from Acquisition import aq_base
from AccessControl.User import UserFolder, User
from Products.CMFCore.utils import getToolByName

#
# Helpers
#

def _preprocessQuery(mapping, search_substring_props):
    """Compute search_types and query."""
    search_types = {}
    query = {}
    for key, value in mapping.items():
        if type(value) is StringType:
            if key in search_substring_props:
                search_types[key] = 'substring'
                value = value.lower()
            else:
                search_types[key] = 'exact'
        else:
            search_types[key] = 'list'
        query[key] = value
    return search_types, query

def _isEntryMatching(entry, search_types, query):
    """Is the entry matching the query?

    Does an AND search for all key, value of the query.
    If the entry value corresponding to a key is a list,
    does an OR search on all the list elements.
    If the query value is a list, does OR search with exact match.
    If the query value is a string, does an case-independent match or a
    substring case independent search depending on search_substring_props,
    searching a substring '*' always match.
    """
    for key, value in query.items():
        if not value:
            # Ignore empty searches.
            continue
        if not entry.has_key(key):
            return 0
        searched = entry[key]
        if searched is None:
            return 0
        if type(searched) is StringType:
            searched = (searched,)
        matched = 0
        for item in searched:
            if search_types[key] == 'list':
                matched = item in value
            elif search_types[key] == 'substring':
                if value == '*':
                    matched = 1
                else:
                    matched = item.lower().find(value) != -1
            else: # search_types[key] == 'exact':
                matched = item == value
            if matched:
                break
        if not matched:
            return 0
    return 1

#
# New APIs
#

# User Folder

def searchUsers(self, query={}, props=None, options={}, **kw):
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
    # The basic implementation doesn't know about properties beside
    # roles and groups.
    kw.update(query)
    query = kw
    do_roles = query.has_key('roles')
    do_groups = query.has_key('groups')
    search_substring_props = options.get('search_substring_props', [])
    search_types, query = _preprocessQuery(query, search_substring_props)
    res = []
    for user in self.getUsers():
        base_user = aq_base(user)
        id = user.getId()
        entry = {'id': id}
        if do_roles:
            roles = user.getRoles()
            entry['roles'] = [r for r in roles
                              if r not in ('Anonymous', 'Authenticated')]
        if do_groups and hasattr(base_user, 'getGroups'):
            entry['groups'] = user.getGroups()
        if not _isEntryMatching(entry, search_types, query):
            continue
        if props is None:
            res.append(id)
        else:
            d = {}
            for key in props:
                if entry.has_key(key):
                    d[key] = entry[key]
            res.append((id, d))
    return res

def listUserProperties(self):
    """Lists properties settable or searchable on the users."""
    return ('id', 'roles', 'groups')

def hasUser(self, user_id):
    raise NotImplementedError

#
# Extended Role management methods for CPS3
#
def setRolesOfUser(self, roles, username):
    """Sets the users of a role"""
    userob = self.getUser(username)
    domains = userob.getDomains()
    self._doChangeUser(username, None, roles, domains)

def setUsersOfRole(self, usernames, role):
    """Sets the users of a role"""
    for user in self.getUserNames():
        userob = self.getUser(user)
        domains = userob.getDomains()
        roles = list(userob.getRoles())
        # If we call _doChangeUser with Authenticated in the roles,
        # user.getRoles() will return Authenticated twice...
        roles.remove('Authenticated')
        if user in usernames and role not in roles:
            roles.append(role)
            self._doChangeUser(user, None, roles, domains)
        elif user not in usernames and role in roles:
            roles.remove(role)
            self._doChangeUser(user, None, roles, domains)

def getUsersOfRole(self, role):
    """Gets the users of a role"""
    users = []
    for username in self.getUserNames():
        user = self.getUser(username)
        if role in user.getRoles():
            users.append(username)
    return users

def userFolderAddRole(self, role):
    """Creates a role"""
    portal = self.aq_inner.aq_parent
    portal._addRole(role)

userfolder_methods = (
    searchUsers,
    listUserProperties,
    #hasUser,
    setRolesOfUser,
    setUsersOfRole,
    getUsersOfRole,
    userFolderAddRole,
    )

# User

def listProperties(self): # ?
    raise NotImplementedError

def hasProperty(self, id):
    raise NotImplementedError

def getProperty(self, id, default=None):
    raise NotImplementedError

def getProperties(self, ids):
    raise NotImplementedError

def setProperty(self, id, value):
    raise NotImplementedError

def setProperties(self, **kw):
    raise NotImplementedError

user_methods = (
    #listProperties,
    #hasProperty,
    #getProperty,
    #getProperties,
    #setProperty,
    #setProperties,
    )

#
# Patching
#

# XXX security!

for meth in userfolder_methods:
    setattr(UserFolder, meth.__name__, meth)

for meth in user_methods:
    setattr(User, meth.__name__, meth)

LOG('UserFolderPatch', TRACE, 'Patching UserFolder and User')
