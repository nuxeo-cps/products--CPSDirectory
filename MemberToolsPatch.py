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
userfolders using a standard API.
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName


#
# Patch of existing APIs
#

# MembershipTool

def addMember(self):
    pass

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


#
# New APIs
#

# MembershipTool
def memberExists(self):
    pass

# MemberDataTool
def searchForMembers(self):
    pass

