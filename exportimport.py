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
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.CPSDirectory.interfaces import IDirectoryTool
from Products.CPSDirectory.interfaces import IDirectory
from Products.CPSDirectory.interfaces import IMetaDirectory
from Products.CPSDirectory.interfaces import IContentishDirectory
from Products.CPSDirectory.interfaces import ILDAPServerAccess

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
                if dir.searchEntries():
                    continue
            parent._delObject(obj_id)


class LDAPServerAccessXMLAdapter(XMLAdapterBase,
                           PostProcessingPropertyManagerHelpers):
    """XML importer and exporter for DirectoryTool.
    """

    adapts(ILDAPServerAccess, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())

        self._logger.info("%r ldap access imported." % self.context.getId())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        self._initProperties(node)
        self._logger.info("%r ldap access exported." % self.context.getId())


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
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractEntryLR())
        if IMetaDirectory.providedBy(self.context):
            node.appendChild(self._extractBackings())
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

    def _extractBackingInfo(self, info):
        fragment = self._doc.createDocumentFragment()
        for b_name, name in info['field_rename'].items():
            child = self._doc.createElement('field-rename')
            child.setAttribute('in-backing', b_name)
            child.setAttribute('in-meta', name)
            fragment.appendChild(child)
        for ignore in info['field_ignore']:
            child = self._doc.createElement('field-ignore')
            child.setAttribute('name', ignore)
            fragment.appendChild(child)
        child = self._doc.createElement('missing-entry-expr')
        child.appendChild(self._doc.createTextNode(info['missing_entry_expr']))
        fragment.appendChild(child)
        return fragment

    def _extractBackings(self):
        fragment = self._doc.createDocumentFragment()
        infos = self.context.getBackingDirectories(no_dir=True)
        for info in infos:
            child = self._doc.createElement('backing')
            child.setAttribute('name', info['dir_id'])
            child.appendChild(self._extractBackingInfo(info))
            fragment.appendChild(child)
        return fragment

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        is_meta = IMetaDirectory.providedBy(self.context)
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeEntryLR()
            if is_meta:
                self._purgeBackings()
            self._purgeCacheableManagerAssociation()

        self._initProperties(node)
        self._initEntryLR(node)
        if is_meta:
            self._initBackings(node)
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

    def _purgeBackings(self):
        self.context.backings_dir_infos = []

    def _initBackingInfo(self, node, bdir_id, new=True):
        field_ignore = []
        field_renames = []
        missing_entry_expr = ''
        for child in node.childNodes:
            if child.nodeName == 'field-ignore':
                field_ignore.append(str(child.getAttribute('name')))
            elif child.nodeName == 'field-rename':
                in_backing = str(child.getAttribute('in-backing'))
                in_meta = str(child.getAttribute('in-meta'))
                field_renames.append(
                    {'b_id': str(child.getAttribute('in-backing')),
                     'id' : str(child.getAttribute('in-meta')),})
            elif child.nodeName == 'missing-entry-expr':
                missing_entry_expr = str(self._getNodeText(child))

        if new:
            meth = self.context.manage_addBacking
        else:
            meth = self.context.manage_changeBacking
        meth(bdir_id, field_ignore, field_renames, missing_entry_expr)

    def _initBackings(self, node):
        mdir = self.context
        existing = [info['dir_id']
                    for info in mdir.getBackingDirectories(no_dir=True)]
        for child in node.childNodes:
            if child.nodeName != 'backing':
                continue
            bdir_id = child.getAttribute('name')
            self._initBackingInfo(child, bdir_id, new=bdir_id not in existing)


class ContentishDirectoryXMLAdapter(DirectoryXMLAdapter):
    """XML importer and exporter for a directory.
    """

    adapts(IContentishDirectory, ISetupEnviron)
    implements(IBody)
