# Copyright (c) 2003 Nuxeo SARL <http://nuxeo.com>
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
"""CPSDirectory init.
"""

from zLOG import LOG, INFO
from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.CMFCorePermissions import ManagePortal

try:
    from Products.LDAPUserGroupsFolder import LDAPDelegate
except ImportError:
    try:
        from Products.LDAPUserFolder import LDAPDelegate
    except ImportError:
        LDAPDelegate = None
has_ldap = (LDAPDelegate is not None)
del LDAPDelegate


from Products.CPSSchemas.VocabulariesTool import VocabularyTypeRegistry

import DirectoryTool

from DirectoryTool import DirectoryTypeRegistry
from MembersDirectory import MembersDirectory
from RolesDirectory import RolesDirectory
from GroupsDirectory import GroupsDirectory

if has_ldap:
    from LDAPDirectory import LDAPDirectory
else:
    LOG('LDAPDirectory', INFO, "Disabled (no LDAP user folder product found).")

from DirectoryVocabulary import DirectoryVocabulary


tools = (DirectoryTool.DirectoryTool,
         )

registerDirectory('skins/cps_directory', globals())

def initialize(registrar):
    ToolInit(
        'CPS Directory Tool',
        tools = tools,
        product_name = 'CPSDirectory',
        icon = 'tool.gif',
        ).initialize(registrar)
    DirectoryTypeRegistry.register(MembersDirectory)
    DirectoryTypeRegistry.register(RolesDirectory)
    DirectoryTypeRegistry.register(GroupsDirectory)
    if has_ldap:
        DirectoryTypeRegistry.register(LDAPDirectory)
    VocabularyTypeRegistry.register(DirectoryVocabulary)
