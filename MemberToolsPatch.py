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
"""MemberToolsPatch

Patches CMF's Membership and MemberData tools to make them access
user folders using a standard API.

APIs used are:
- userFolderAddUser
- listUserProperties
- searchUsers

"""

from zLOG import LOG, TRACE, DEBUG

from types import StringType

from Acquisition import aq_base

from Products.CMFCore.MembershipTool import MembershipTool
from Products.CMFCore.MemberDataTool import MemberDataTool

_marker = []


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
    substring case independent search depending on search_substring_props.
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
                matched = item.lower().find(value) != -1
            else: # search_types[key] == 'exact':
                matched = item == value
            if matched:
                break
        if not matched:
            return 0
    return 1

def _searchInMemberData(self, query, props=None, search_substring_props=[]):
    """Search members using only MemberData._members."""
    search_types, query = _preprocessQuery(query, search_substring_props)
    mdtool = self
    mdtool_props = mdtool.propertyIds()
    checked_props = [p for p in mdtool_props if query.has_key(p)]
    if props == ['*']:
        # all props known other than already fetched by the search
        other_props = [p for p in mdtool_props if p not in checked_props]
    elif props is not None:
        # all props asked for other than already fetched by the search
        other_props = [p for p in props if p not in checked_props]

    res = []
    for id, member in mdtool._members.items():
        base_member = aq_base(member)
        entry = {'id': id}
        for key in checked_props:
            searched = getattr(base_member, key, _marker)
            if searched is _marker:
                # default value
                searched = mdtool.getProperty(key)
            entry[key] = searched
        if not _isEntryMatching(entry, search_types, query):
            continue
        if props is None:
            res.append(id)
        elif props == ['*']:
            res.append((id, entry))
        else:
            for key in other_props:
                value = getattr(base_member, key, _marker)
                if value is _marker:
                    # default value
                    value = mdtool.getProperty(key)
                entry[key] = value
            res.append((id, entry))
    return res

#
# New APIs
#

# MembershipTool
def hasMember(self, member_id):
    raise NotImplementedError

# MemberDataTool
def searchForMembers(self, query={}, props=None, options={}, **kw):
    """Search for members.

    If props is None, returns a list of ids:
      ['member1', 'member2']

    If props is not None, it must be sequence of property ids. The
    method will return a list of tuples containing the member id and a
    dictionary of available properties:
      [('member1', {'email': 'foo', 'age': 75}), ('member2', {'age': 5})]

    props=['*'] means to return all available properties.

    options is a dictionnary with keys:
      - search_substring_props: the props where search has to be done
        by substring.

    """
    kw.update(query)
    query = kw
    aclu = self.acl_users

    done_props = []
    done_query_keys = []

    LOG('searchForMembers', DEBUG, 'query=%s props=%s' % (query, props))

    # Do the search on the attributes known to the user object.

    if hasattr(aq_base(aclu), 'listUserProperties'):
        # Search in the user folder.
        aclu_props = aclu.listUserProperties()
        if props is None:
            user_props = None
        elif props == ['*']:
            user_props = list(aclu_props)
        else:
            user_props = [p for p in props if p in aclu_props]
        user_query = {}
        for key, value in query.items():
            if key in aclu_props:
                user_query[key] = value
        LOG('searchForMembers', DEBUG, 'user_query=%s user_props=%s' %
            (user_query, user_props))
        if user_query:
            users_res = aclu.searchUsers(user_query, props=user_props,
                                         options=options)
            done_props.extend(aclu_props)
            done_query_keys.extend(user_query.keys())
        else:
            # XXX incorrect if user_props exists !!!
            users_res = None

    else:
        # Not a user folder with search API, we can't search it.
        users_res = None
    LOG('searchForMembers', DEBUG, "users_res=%s done_props=%s done_query_keys=%s" % (users_res, done_props, done_query_keys))

    # Do the search in the local MemberData.

    mdtool = self
    mdtool_props = mdtool.propertyIds()
    if props is None:
        member_props = None
    elif props == ['*']:
        member_props = [p for p in mdtool_props if p not in done_props]
    else:
        member_props = [p for p in props
                        if p in mdtool_props and p not in done_props]
    member_query = {}
    for key, value in query.items():
        if key in mdtool_props and key not in done_query_keys:
            member_query[key] = value
    LOG('searchForMembers', DEBUG, 'member_query=%s member_props=%s' %
        (member_query, member_props))
    if member_query:
        search_substring_props = options.get('search_substring_props', [])
        members_res = _searchInMemberData(
            self, member_query,
            props=member_props,
            search_substring_props=search_substring_props)
        done_props.extend(mdtool_props)
        done_query_keys.extend(member_query.keys())
    else:
        # XXX incorrect if member_props exists !!!
        members_res = None

    LOG('searchForMembers', DEBUG, "members_res=%s done_props=%s done_query_keys=%s" % (members_res, done_props, done_query_keys))


    # Now merge the results
    # Keep members that are in both, and merge their info.
    if users_res is None:
        res = members_res
    elif members_res is None:
        res = users_res
    else: # use both users_res and members_res
        if len(users_res) < len(members_res):
            small, big = users_res, members_res
        else:
            small, big = members_res, users_res
        if props is None:
            res = [id for id in small if id in big]
        else:
            bigasdict = {}
            for id, d in big:
                bigasdict[id] = d
            res = []
            for id, d in small:
                if not bigasdict.has_key(id):
                    continue
                d.update(bigasdict[id])
                res.append((id, d))

    if res is None:
        # Search corresponding to no known property.
        res = []

    return res

#
# Existing APIs made more generic
#

# MembershipTool

def addMember(self, id, password, roles, domains, properties=None,
              groups=None):
    """Add a new member.

    The member is created with the specified id, password, roles,
    domains, groups. The specified properties are assigned to it.
    """
    # XXX Should we optimize to create and set props in one step if
    # possible (think LDAP) ? Is it worth it ?

    acl_users = self.acl_users
    props = properties or {}
    if groups is not None:
        props = props.copy()
        props['groups'] = groups

    if hasattr(aq_base(acl_users), 'userFolderAddUser'):
        # Standardized user folder API.
        acl_users.userFolderAddUser(id, password, roles, domains, **props)
    elif hasattr(aq_base(acl_users), '_addUser'):
        acl_users._addUser(id, password, password, roles, domains, **props)
    else:
        raise ValueError("Can't add Member, unsupported user folder")

    if properties:
        member = self.getMemberById(id)
        if hasattr(aq_base(member), 'setMemberProperties'):
            member.setMemberProperties(properties)

membershiptool_methods = (
    #addMember,
    )

# MemberDataTool

def wrapUser(self, user):
    """If possible, returns the Member object that corresponds
    to the given User object.
    """
    raise NotImplementedError

memberdatatool_methods = (
    searchForMembers,
    )

# MemberData

def setMemberProperties(self, mapping):
    """Set the properties of the member."""
    raise NotImplementedError

def setSecurityProfile(self, password=None, roles=None, domains=None):
    """Set the user's basic security profile."""
    raise NotImplementedError

def getPassword(self):
    """Return the password of the user."""
    raise NotImplementedError


#
# Patching
#

# XXX security!

for meth in membershiptool_methods:
    setattr(MembershipTool, meth.__name__, meth)

for meth in memberdatatool_methods:
    setattr(MemberDataTool, meth.__name__, meth)

LOG('MemberToolsPatch', TRACE, 'Patching Member Tools')
