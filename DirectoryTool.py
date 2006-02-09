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
from AccessControl import Unauthorized
from AccessControl.PermissionRole import PermissionRole

import Products
from OFS.Folder import Folder
from OFS.ObjectManager import IFAwareObjectManager
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal

from Products.CPSDirectory.BaseDirectory import BaseDirectory

from Products.CPSDirectory.interfaces import IDirectory
from Products.CPSDirectory.interfaces import IContentishDirectory
from Products.CPSDirectory.interfaces import IDirectoryTool

from zope.interface import implements


class DirectoryTool(UniqueObject, IFAwareObjectManager, Folder):
    """Directory Tool

    Stores directories.
    """

    implements(IDirectoryTool)

    id = 'portal_directories'
    meta_type = 'CPS Directory Tool'
    _product_interfaces = (IDirectory, IContentishDirectory)

    security = ClassSecurityInfo()

    def __init__(self):
        pass

    #
    # API
    #

    security.declarePublic('listVisibleDirectories')
    def listVisibleDirectories(self):
        """List directories visible by the current user.

        Returns a list of directory ids.
        """
        res = []
        for dir_id, dir in self.objectItems():
            if dir.meta_type == 'Broken Because Product is Gone':
                continue
            if not isinstance(dir, BaseDirectory):
                continue
            if dir.isVisible():
                res.append(dir_id)
        res.sort()
        return res

    #
    # ZMI
    #

    def all_meta_types(self):
        # Get matching from IFAwareObjectManager
        all = IFAwareObjectManager.all_meta_types(self)
        # Add a few others
        for mt in Products.meta_types:
            name = mt['name']
            if (name.startswith('Z') and
                name.endswith('Database Connection')):
                all.append(mt)
            elif name.endswith('RAM Cache Manager'):
                all.append(mt)
        return all

    # BBB for old installers/importers, will be removed in CPS 3.5
    security.declarePrivate('manage_addCPSDirectory')
    def manage_addCPSDirectory(self, id, meta_type, **kw):
        import Products
        for mt in Products.meta_types:
            if mt['name'] == meta_type:
                klass = mt['instance']
                self._setObject(id, klass(id, **kw))
                return self._getOb(id)
        raise ValueError("Unknown meta_type %r" % meta_type)

InitializeClass(DirectoryTool)


# BBB for old installers/importers, will be removed in CPS 3.5
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
