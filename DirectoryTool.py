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
"""Directory Tool

The Directory Tool manages directories.
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo

from OFS.Folder import Folder

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.CMFCorePermissions import ManagePortal


class DirectoryTool(UniqueObject, Folder):
    """Directory Tool

    Stores directories.
    """

    id = 'portal_directories'
    meta_type = 'CPS Directory Tool'

    security = ClassSecurityInfo()

    def __init__(self):
        pass

    #
    # ZMI
    #

    def all_meta_types(self):
        # Stripping is done to be able to pass a type in the URL.
        return [
            {'name': dt,
             'action': 'manage_addCPSDirectoryForm/' + dt.replace(' ', ''),
             'permission': ManagePortal}
            for dt in DirectoryTypeRegistry.listTypes()]

    security.declareProtected(ManagePortal, 'manage_addCPSDirectoryForm')
    manage_addCPSDirectoryForm = DTMLFile('zmi/directory_addform', globals())

    security.declareProtected(ManagePortal, 'manage_addCPSDirectory')
    def manage_addCPSDirectory(self, id, meta_type, REQUEST=None):
        """Add a directory, called from the ZMI."""
        container = self
        cls = DirectoryTypeRegistry.getType(meta_type)
        ob = cls(id)
        container._setObject(id, ob)
        ob = container._getOb(id)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(ob.absolute_url()+'/manage_workspace'
                                      '?manage_tabs_message=Added.')
        else:
            return ob

    security.declareProtected(ManagePortal, 'getDirectoryMetaType')
    def getDirectoryMetaType(self, meta_type):
        """Get an unstripped version of a directory meta type."""
        return DirectoryTypeRegistry.getType(meta_type).meta_type

InitializeClass(DirectoryTool)


class DirectoryTypeRegistry:
    """Registry of the available directory types.

    Internally strips spaces, to be able to use arguments extracted from
    URL components.
    """

    def __init__(self):
        self._types = {}

    def register(self, cls):
        """Register a directory type."""
        mt = cls.meta_type.replace(' ', '')
        self._types[mt] = cls

    def listTypes(self):
        """List directory types."""
        types = [cls.meta_type for cls in self._types.values()]
        types.sort()
        return types

    def getType(self, meta_type):
        """Get a directory type."""
        mt = meta_type.replace(' ', '')
        return self._types[mt]

# Singleton
DirectoryTypeRegistry = DirectoryTypeRegistry()
