# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
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
"""Directory tool import/export for CMFSetup.
"""

import os
from Globals import package_home
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName

from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CMFSetup.utils import ConfiguratorBase
from Products.CMFSetup.utils import CONVERTER, DEFAULT, KEY

_pkgdir = package_home(globals())
_xmldir = os.path.join(_pkgdir, 'xml')


_FILENAME = 'directories.xml'


def importDirectoryTool(context):
    """Import directories."""
    site = context.getSite()
    encoding = context.getEncoding()
    tool = getToolByName(site, 'portal_directories')

    if context.shouldPurge():
        for dir_id in _getDirectoryIds(tool):
            # XXX
            # Ensure we don't remove a directory with some conf in it
            # Remove it by hand before importing, it's safer.
            if len(tool[dir_id].objectIds()):
                raise ValueError("Directory %s not empty, aborting import"
                                 % dir_id)
            tool._delObject(dir_id)

    text = context.readDataFile(_FILENAME)
    if text is None:
        return "Directories: nothing to import."

    dtconf = DirectoryToolConfigurator(site, encoding)
    tool_info = dtconf.parseXML(text)
    dconf = DirectoryImportConfigurator(site, encoding)

    for info in tool_info['directories']:
        dir_id = str(info['id'])
        filename = info['filename']
        sep = filename.rfind( '/' )
        if sep == -1:
            dir_text = context.readDataFile(filename)
        else:
            dir_text = context.readDataFile(filename[sep+1:],
                                            filename[:sep])
        dir_info = dconf.parseXML(dir_text)

        dir = tool.manage_addCPSDirectory(dir_id, dir_info['kind'])
        for prop_info in dir_info['properties']:
            dconf.initProperty(dir, prop_info)
        dir._postProcessProperties()
        for elr in dir_info['entry-local-roles']:
            res = dir.addEntryLocalRole(elr['role'], elr['expr'])
            if res:
                raise ValueError(res)

    return "Directories imported."


def exportDirectoryTool(context):
    """Export directories as a set of XML files."""
    site = context.getSite()
    tool = getToolByName(site, 'portal_directories')

    dtconf = DirectoryToolConfigurator(site).__of__(site)

    tool_xml = dtconf.generateXML()
    context.writeDataFile(_FILENAME, tool_xml, 'text/xml')

    for info in dtconf.listDirectoryInfo():
        dir_id = info['id']
        dir = tool[dir_id]
        dconf = DirectoryExportConfigurator(dir, site).__of__(site)
        dir_xml = dconf.generateXML()
        context.writeDataFile(_getDirectoryFilename(dir_id),
                              dir_xml, 'text/xml',
                              _getDirectoryDir(dir_id))
    return "Directories exported."


class DirectoryToolConfigurator(ConfiguratorBase):
    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'listDirectoryInfo')
    def listDirectoryInfo(self):
        """Return a list of mappings for directories in the site."""
        result = []
        tool = getToolByName(self._site, 'portal_directories')
        for dir_id in _getDirectoryIds(tool):
            info = {'id': dir_id}
            #filename = _getDirectoryFilename(dir_id)
            #if filename != dir_id:
            #    info['filename'] = filename
            result.append(info)
        return result

    def _getExportTemplate(self):
        return PageTemplateFile('directoryToolExport.xml', _xmldir)

    def _getImportMapping(self):
        return {
            'directory-tool': {
                'directory': {KEY: 'directories', DEFAULT: (),
                              CONVERTER: self._convertDirectories},},
            'directory': {
                'id': {},
                'filename': {DEFAULT: ''},},
            }

    def _convertDirectories(self, val):
        for dir in val:
            if not dir['filename']:
                dir['filename'] = _getDirectoryPath(dir['id'])
        return val

InitializeClass(DirectoryToolConfigurator)


class DirectoryImportConfigurator(ConfiguratorBase):
    """Directory configurator for a given directory.
    """
    def _getExportTemplate(self): # XXX artefact
        return None

    def _getImportMapping(self):
        return {
            'directory': {
                'kind': {},
                'property': {KEY: 'properties', DEFAULT: ()},
                'entry-local-role': {KEY: 'entry-local-roles', DEFAULT: ()},
                },
            'entry-local-role': {
                'role': {},
                '#text': {KEY: 'expr'},
                },
            }

InitializeClass(DirectoryImportConfigurator)


class DirectoryExportConfigurator(ConfiguratorBase):
    """Directory export configurator for a given directory.
    """
    security = ClassSecurityInfo()

    def __init__(self, dir, *args, **kw):
        self.dir = dir
        ConfiguratorBase.__init__(self, *args, **kw)

    security.declareProtected(ManagePortal, 'getDirectoryKind')
    def getDirectoryKind(self):
        """Return the directory type."""
        return self.dir.meta_type

    security.declareProtected(ManagePortal, 'getDirectoryPropsXML')
    def getDirectoryPropsXML(self):
        """Return props as XML."""
        dir = self.dir
        prop_infos = [self._extractProperty(dir, prop_map)
                      for prop_map in dir._propertyMap()]
        return self.generatePropertyNodes(prop_infos)

    security.declareProtected(ManagePortal, 'getDirectoryEntryLR')
    def getDirectoryEntryLR(self):
        """Return entry local roles."""
        return [{'role': role, 'expr': expr}
                for role, expr in self.dir.listEntryLocalRoles()]

    def _getExportTemplate(self):
        return PageTemplateFile('directoryExport.xml', _xmldir)

InitializeClass(DirectoryExportConfigurator)


def _getDirectoryDir(dir_id):
    """Return the folder name for the directories files."""
    return 'directories'

def _getDirectoryFilename(dir_id):
    """Return the file name holding info for a given directory."""
    return dir_id.replace(' ', '_') + '.xml'

def _getDirectoryPath(dir_id):
    """Return the file path holding info for a given directory."""
    base = _getDirectoryDir(dir_id)
    file = _getDirectoryFilename(dir_id)
    if base:
        return base+'/'+file
    else:
        return file

def _getDirectoryIds(tool):
    result = []
    for dir_id, dir in tool.objectItems():
        if dir.meta_type == 'Broken Because Product is Gone':
            continue
        if not isinstance(dir, BaseDirectory):
            continue
        result.append(dir_id)
    return result
