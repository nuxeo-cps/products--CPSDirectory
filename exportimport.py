# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
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
"""Directory Tool XML Adapter.
"""

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.CPSUtil.PropertiesPostProcessor import (
    PostProcessingPropertyManagerHelpers)

from zope.component import adapts
from zope.interface import implements
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.CPSDirectory.interfaces import IDirectoryTool
from Products.CPSDirectory.interfaces import IDirectory


TOOL = 'portal_directories'
NAME = 'directories'

def exportDirectoryTool(context):
    """Export directory tool and directories as a set of XML files.
    """
    site = context.getSite()
    tool = getToolByName(site, TOOL, None)
    if tool is None:
        logger = context.getLogger(NAME)
        logger.info("Nothing to export.")
        return
    exportObjects(tool, '', context)

def importDirectoryTool(context):
    """Import directory tool and directories from XML files.
    """
    site = context.getSite()
    tool = getToolByName(site, TOOL)
    importObjects(tool, '', context)


class DirectoryToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                              PropertyManagerHelpers):
    """XML importer and exporter for DirectoryTool.
    """

    adapts(IDirectoryTool, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME
    name = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())

        self._logger.info("Directory tool exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeObjects()

        self._initProperties(node)
        self._initObjects(node)
        self._logger.info("Directory tool imported.")

class DirectoryXMLAdapter(XMLAdapterBase,
                          PostProcessingPropertyManagerHelpers):
    """XML importer and exporter for a directory.
    """

    adapts(IDirectory, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractEntryLR())

        self._logger.info("%r directory exported." % self.context.getId())
        return node

    def _extractEntryLR(self):
        fragment = self._doc.createDocumentFragment()
        entry_lr = self.context.listEntryLocalRoles()
        entry_lr.sort()
        for role, expr in entry_lr:
            child = self._doc.createElement('entry-local-roles')
            child.setAttribute('role', role)
            child.appendChild(self._doc.createTextNode(expr))
            fragment.appendChild(child)
        return fragment


    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeEntryLR()

        self._initProperties(node)
        self._initEntryLR(node)

        self._logger.info("%r directory imported." % self.context.getId())

    def _purgeEntryLR(self):
        self.context.entry_roles = []

    def _initEntryLR(self, node):
        for child in node.childNodes:
            if child.nodeName != 'entry-local-roles':
                continue
            role = str(child.getAttribute('role'))
            expr = self._getNodeText(child)
            res = self.context.addEntryLocalRole(role, expr)
            if res:
                # Compilation problem
                raise ValueError(res)
