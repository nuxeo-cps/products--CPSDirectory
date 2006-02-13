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
from Products.CPSUtil.cachemanagersetup import CacheableHelpers

from zope.component import adapts
from zope.interface import implements
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import INode
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.CPSDirectory.interfaces import IDirectoryTool
from Products.CPSDirectory.interfaces import IDirectory
from Products.CPSDirectory.interfaces import IDirectoryEntry
from Products.CPSDirectory.interfaces import IContentishDirectory

from zope.app import zapi

import Products

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

    def _purgeObjects(self):
        parent = self.context
        for obj_id in parent.objectIds():
            dir = parent._getOb(obj_id)
            # it's a Directory with content (potentially)
            if IContentishDirectory.providedBy(dir):
                # if the directory has entries, don't delete it
                if dir._searchEntries():
                    continue
            parent._delObject(obj_id)


class DirectoryXMLAdapter(XMLAdapterBase, CacheableHelpers,
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
        node.appendChild(self._extractObjects())
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractEntryLR())
        child = self._extractCacheableManagerAssociation()
        if child is not None:
            node.appendChild(child)

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
            self._purgeCacheableManagerAssociation()

        self._initProperties(node)
        self._initEntryLR(node)
        self._initCacheableManagerAssociation(node)

        self._logger.info("%r directory imported." % self.context.getId())

    def _purgeEntryLR(self):
        self.context.entry_roles = []

    def _initEntryLR(self, node):
        for child in node.childNodes:
            if child.nodeName != 'entry-local-role':
                continue
            role = str(child.getAttribute('role'))
            expr = self._getNodeText(child)
            # delete if it exists
            self.context.delEntryLocalRole(role)
            res = self.context.addEntryLocalRole(role, expr)
            if res:
                # Compilation problem
                raise ValueError(res)

class ContentishDirectoryXMLAdapter(DirectoryXMLAdapter):
    """XML importer and exporter for a directory.
    """

    adapts(IContentishDirectory, ISetupEnviron)
    implements(IBody)

    def _extractObjects(self):
        fragment = self._doc.createDocumentFragment()
        for item in self.context._searchEntries():
            entry = self.context._getOb(item)
            exporter = zapi.queryMultiAdapter((entry, self.environ), INode)
            if not exporter:
                raise ValueError("Entry %s cannot be adapted to INode" % entry)
            fragment.appendChild(exporter.node)
        return fragment

    def _initObjects(self, node):
        parent = self.context
        entries = parent._searchEntries()
        for child in node.childNodes:
            if child.nodeName != 'object':
                continue
            if child.hasAttribute('deprecated'):
                continue
            obj_id = str(child.getAttribute('name'))
            if obj_id not in entries:
                meta_type = str(child.getAttribute('meta_type'))
                __traceback_info__ = obj_id, meta_type
                for mt_info in Products.meta_types:
                    if mt_info['name'] == meta_type:
                        parent._setObject(obj_id, mt_info['instance'](obj_id))
                        break
                else:
                    raise ValueError("unknown meta_type '%s'" % meta_type)
            obj = getattr(parent, obj_id)
            importer = zapi.queryMultiAdapter((obj, self.environ), INode)
            if importer:
                importer.node = child

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractObjects())
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractEntryLR())
        child = self._extractCacheableManagerAssociation()
        if child is not None:
            node.appendChild(child)

        self._logger.info("%r directory exported." % self.context.getId())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self._initProperties(node)
        self._initEntryLR(node)
        self._initObjects(node)

        self._logger.info("%r directory imported." % self.context.getId())


class DirectoryEntryXMLAdapter(XMLAdapterBase,
                               PropertyManagerHelpers):
    """XML importer and exporter for a directory.
    """

    adapts(IDirectoryEntry, ISetupEnviron)
    implements(IBody)
    __used_for__ = IDirectoryEntry

    _LOGGER_ID = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        # XXX: maybe extractObject isn't needed, after all
        node.appendChild(self._extractProperties())
        self._logger.info("%r directory entry exported." % self.context.getId())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        self._initProperties(node)
        self._logger.info("%s imported." % self.context.getId())

    def _extractProperties(self):
        fragment = self._doc.createDocumentFragment()
        entry = self.context
        self._logger.info("directory entry: %s" % entry)

        for key, value in entry.__dict__.items():
            ### FIXME: maybe _owner should be exported
            if key not in ['__name__', 'id', '_owner']:
                node = self._doc.createElement('property')
                node.setAttribute('name', key)
                if isinstance(value, (tuple, list)):
                    for item in value:
                        child = self._doc.createElement('element')
                        # XXX item should be encoded?
                        child.setAttribute('value', item.decode('ISO-8859-15').encode('utf-8'))
                        node.appendChild(child)
                else:
                    if isinstance(value, bool):
                        prop = str(bool(value))
                    elif isinstance(value, basestring):
                        # XXX value should be encoded?
                        prop = str(value.decode('ISO-8859-15').encode('utf-8'))
                    else:
                        raise ValueError("item: {'%s': '%s'} cannot be exported" % (key, value))
                    child = self._doc.createTextNode(prop)
                    node.appendChild(child)
                fragment.appendChild(node)
        return fragment

    def _initProperties(self, node):
        ### TODO to be implemented
        pass