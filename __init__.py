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

from Products.CMFCore.utils import ToolInit
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.CMFCorePermissions import ManagePortal


import DirectoryTool

from DirectoryTool import DirectoryTypeRegistry
from MembersDirectory import MembersDirectory

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
