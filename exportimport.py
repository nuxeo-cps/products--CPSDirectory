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

from zope.app import zapi

from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers
from Products.CMFCore.utils import getToolByName

from Products.GenericSetup.interfaces import IBody
from Products.CPSDirectory.interfaces import IDirectoryTool
from Products.CPSDirectory.interfaces import IDirectory

_FILENAME = 'directories.xml'


def exportDirectoryTool(context):
    """Export directory tool and directories as a set of XML files.
    """
    site = context.getSite()
    logger = context.getLogger('directories')
    tool = getToolByName(site, 'portal_directories', None)
    if tool is None:
        logger.info("Nothing to export.")
        return

    exporter = zapi.queryMultiAdapter((tool, context), IBody)
    if exporter is None:
        logger.warning("Export adapter misssing.")
        return

    context.writeDataFile(_FILENAME, exporter.body, exporter.mime_type)
    exportObjects(tool, 'directories', context)


def importDirectoryTool(context):
    """Import directory tool and directories from XML files.
    """
    site = context.getSite()
    logger = context.getLogger('directories')
    tool = getToolByName(site, 'portal_directories')

    body = context.readDataFile(_FILENAME)
    if body is None:
        logger.info("Nothing to import.")
        return

    importer = zapi.queryMultiAdapter((tool, context), IBody)
    if importer is None:
        logger.warning("Import adapter misssing.")
        return

    importer.body = body
    importObjects(tool, 'directories', context)


class DirectoryToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                              PropertyManagerHelpers):
    """XML importer and exporter for DirectoryTool.
    """

    # BBB: use adapts() in 2.9
    __used_for__ = IDirectoryTool

    _LOGGER_ID = 'directories'

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

class DirectoryXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    """XML importer and exporter for a directory.
    """

    # BBB: use adapts() in 2.9
    __used_for__ = IDirectory

    _LOGGER_ID = 'directories'

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
            child = self._doc.createElement('entry-local-role')
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
