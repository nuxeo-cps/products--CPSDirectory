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

from Products.CPSUtil.genericsetup import PropertiesSubObjectsXMLAdapter
from Products.CPSUtil.genericsetup import tool_steps
from Products.CPSUtil.property import PostProcessingPropertyManagerHelpers
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
from Products.CPSDirectory.interfaces import IPluggableConnection

TOOL = 'portal_directories'
NAME = 'directories'

exportDirectoryTool, importDirectoryTool = tool_steps(TOOL)

class DirectoryToolXMLAdapter(PropertiesSubObjectsXMLAdapter):
    """XML importer and exporter for DirectoryTool.
    """

    def _purgeObjects(self):
        parent = self.context
        for obj_id in parent.objectIds():
            dir = parent._getOb(obj_id)
            # it's a Directory with content (potentially)
            if IContentishDirectory.providedBy(dir):
                # GR see #1976
                self._logger.warning("Contentish directory %s not removed."
                                     " Do it manually after the import"
                                     " if you really want to" % dir.getId())
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
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractEntryLR())

        # TODO heard about what an adapter is ?
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

class SQLConnectorXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    adapts(IPluggableConnection, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = NAME

    def _exportNode(self):
        """Export the object as a DOM node.

        Manual mapping here, because the connector doesn't have
        property mappers.
        """
        node = self._getObjectNode('object')
        fragment = self._doc.createDocumentFragment()
        for prop_id in ('title', 'connection_string'):
            prop = getattr(self.context, prop_id)
            subnode = self._doc.createElement('property')
            subnode.setAttribute('name', prop_id)
            child = self._doc.createTextNode(prop)
            subnode.appendChild(child)
            fragment.appendChild(subnode)

        # adding check to 1
        subnode = self._doc.createElement('property')
        subnode.setAttribute('name', 'check')
        connected = self.context.connected() is not None
        child = self._doc.createTextNode(str(connected))
        subnode.appendChild(child)
        fragment.appendChild(subnode)

        node.appendChild(fragment)
        self._logger.info("%r connector exported." % self.context.getId())
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()

        obj = self.context
        values = {}
        for child in node.childNodes:
            if child.nodeName != 'property':
                continue
            prop_id = str(child.getAttribute('name'))
            if prop_id in ('title', 'connection_string', 'check'):
                prop_value = self._getNodeText(child).encode('utf-8')
                values[prop_id] = prop_value

        if 'check' not in values:
            values['check'] = False
        else:
            values['check'] = bool(values['check'])
        try:
            from _mysql_exceptions import OperationalError
            try:
                obj.edit(values['title'], values['connection_string'], values['check'])
            except OperationalError:
                obj.title = values['title']
        except ImportError:
            obj.title = values['title']

        self._logger.info("%r connector imported." % self.context.getId())
