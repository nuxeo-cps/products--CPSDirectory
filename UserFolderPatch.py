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

from AccessControl.User import UserFolder, User

#
# New APIs
#

# User Folder

def searchUsers(self, mapping, attributes=(), **kw):
    pass

def hasUser(self, user_id):
    pass

userfolder_methods = (
    searchUsers,
    hasUser,
    )

# User

def listProperties(self): # ?
    pass

def hasProperty(self, id):
    pass

def getProperty(self, id, default=None):
    pass

def getProperties(self, ids):
    pass

def setProperty(self, id, value):
    pass

def setProperties(self, **kw):
    pass

user_methods = (
    listProperties,
    hasProperty,
    getProperty,
    getProperties,
    setProperty,
    setProperties,
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
