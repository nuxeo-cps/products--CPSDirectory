# Copyright (c) 2003-2007 Nuxeo SAS <http://nuxeo.com>
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
"""CPSDirectory init.
"""

import sys

from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CPSUtil.testing.environment import setTestingEnvironmentIfNeeded

# for tests
setTestingEnvironmentIfNeeded()

try:
    import ldap
    has_ldap = 1
except ImportError:
    has_ldap = 0

# Generic setup patches for SQL Connector
import SQLConnector

import DirectoryTool
# Register fields
import DirectoryFields

from DirectoryTool import DirectoryTypeRegistry
from ZODBDirectory import ZODBDirectory
from MembersDirectory import MembersDirectory
from RolesDirectory import RolesDirectory
from GroupsDirectory import GroupsDirectory
from LocalDirectory import LocalDirectory
from MetaDirectory import MetaDirectory
from StackingDirectory import StackingDirectory
from SQLDirectory import SQLDirectory
from IndirectDirectory import IndirectDirectory

if has_ldap:
    from LDAPBackingDirectory import LDAPBackingDirectory


# Vocabularies
from DirectoryVocabulary import DirectoryVocabulary
from DirectoryEntryVocabulary import DirectoryEntryVocabulary
from IndirectDirectoryVocabulary import IndirectDirectoryVocabulary


# register directory specific methods to the FieldNamespace utility
import FieldNamespace

import UserFolderPatch
import MemberToolsPatch

tools = (DirectoryTool.DirectoryTool,)

registerDirectory('skins/cps_directory', globals())

def initialize(registrar):
    ToolInit(
        'CPS Directory Tool',
        tools = tools,
        icon = 'tool.png',
        ).initialize(registrar)
    DirectoryTypeRegistry.register(ZODBDirectory)
    DirectoryTypeRegistry.register(MembersDirectory)
    DirectoryTypeRegistry.register(RolesDirectory)
    DirectoryTypeRegistry.register(GroupsDirectory)
    DirectoryTypeRegistry.register(LocalDirectory)
    DirectoryTypeRegistry.register(MetaDirectory)
    DirectoryTypeRegistry.register(StackingDirectory)
    DirectoryTypeRegistry.register(SQLDirectory)
    if has_ldap:
        DirectoryTypeRegistry.register(LDAPBackingDirectory)
    DirectoryTypeRegistry.register(IndirectDirectory)
