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


#
# Helpers
#

def _preprocessQuery(mapping):
    """Compute is_list_search and query."""
    is_list_search = {}
    query = {}
    for key, value in mapping.items():
        if type(value) is StringType:
            is_list_search[key] = 0
            query[key] = value.lower()
        else:
            is_list_search[key] = 1
            query[key] = value
    return is_list_search, query

def _isEntryMatching(entry, is_list_search, query):
    """Is the entry matching the query?

    Does an AND search for all key, value of the query.
    If the entry value corresponding to a key is a list,
    does an OR search on all the list elements.
    If the query value is a string, does a substring lowercase search.
    If the query value is a list, does OR search with exact match.
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
            if is_list_search[key]:
                matched = item in value
            else:
                matched = item.lower().find(value) != -1
            if matched:
                break
        if not matched:
            return 0
    return 1

#
# New APIs
#

# User Folder

def searchUsers(self, query={}, props=None, options=None, **kw):
    """Search for users having certain properties.

    If props is None, returns a list of ids:
      ['user1', 'user2']

    If props is not None, it must be sequence of property ids. The
    method will return a list of tuples containing the user id and a
    dictionary of available properties:
      [('user1', {'email': 'foo', 'age': 75}), ('user2', {'age': 5})]

    Options is used to specify the search type if possible. XXX
    """
    # The basic implementation doesn't know about properties beside
    # roles and groups.
    query.update(kw)
    do_roles = query.has_key('roles')
    do_groups = query.has_key('groups')
    is_list_search, query = _preprocessQuery(query)
    res = {}
    for user in self.getUsers():
        base_user = aq_base(user)
        id = user.getId()
        entry = {'id': id}
        if do_roles:
            entry['roles'] = user.getRoles()
        if do_groups and hasattr(base_user, 'getGroups'):
            entry['groups'] = user.getGroups()
        if not _isEntryMatching(entry, is_list_search, query):
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

userfolder_methods = (
    searchUsers,
    listUserProperties,
    #hasUser,
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
