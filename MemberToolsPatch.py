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
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName


#
# New APIs
#

# MembershipTool
def hasMember(self, member_id):
    pass

# MemberDataTool
def searchForMembers(mapping, attributes=(), options=None, **kw):
    pass

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

# MemberDataTool

def wrapUser(self, user):
    """If possible, returns the Member object that corresponds
    to the given User object.
    """
    pass

# MemberData

def setMemberProperties(self, mapping):
    """Set the properties of the member."""
    pass

def setSecurityProfile(self, password=None, roles=None, domains=None):
    """Set the user's basic security profile."""
    pass

def getPassword(self):
    """Return the password of the user."""
    pass
