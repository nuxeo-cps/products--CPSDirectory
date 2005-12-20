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

from zope.app import zapi
from xml.dom.minidom import parseString
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.browser.utils import AddWithPresettingsViewBase
from Products.GenericSetup.interfaces import IBody

class BaseAddView(AddWithPresettingsViewBase):
    """Add view for FactoryTypeInformation.
    """

    _dir_name = 'directories'

    description = u"A directory holds tabular information."

    def getProfileInfos(self):
        profiles = []
        stool = getToolByName(self, 'portal_setup', None)
        if stool:
            for info in stool.listContextInfos():
                obj_ids = []
                context = stool._getImportContext(info['id'])
                file_ids = context.listDirectory(self._dir_name)
                for file_id in file_ids or ():
                    filename = self._dir_name + '/' + file_id
                    body = context.readDataFile(filename)
                    if body is None:
                        continue
                    root = parseString(body).documentElement
                    obj_id = root.getAttribute('name')
                    if not obj_id:
                        obj_id = root.getAttribute('id')
                    if root.getAttribute('meta_type') != self.klass.meta_type:
                        continue
                    obj_ids.append(obj_id)
                if not obj_ids:
                    continue
                obj_ids.sort()
                profiles.append({'id': info['id'],
                                 'title': info['title'],
                                 'obj_ids': tuple(obj_ids)})
        return tuple(profiles)

    def _initSettings(self, obj, profile_id, obj_path):
        stool = getToolByName(self, 'portal_setup', None)
        if stool is None:
            return

        context = stool._getImportContext(profile_id)
        file_ids = context.listDirectory(self._dir_name)
        for file_id in file_ids or ():
            filename = self._dir_name + '/' + file_id
            body = context.readDataFile(filename)
            if body is None:
                continue

            root = parseString(body).documentElement
            new_id = root.getAttribute('name')
            if not new_id:
                new_id = root.getAttribute('id')
            if new_id != obj_path[0]:
                continue

            if root.getAttribute('meta_type') != self.klass.meta_type:
                continue

            importer = zapi.queryMultiAdapter((obj, context), IBody)
            if importer is None:
                continue

            importer.body = body
            return


from Products.CPSDirectory.MembersDirectory import MembersDirectory
from Products.CPSDirectory.GroupsDirectory import GroupsDirectory
from Products.CPSDirectory.RolesDirectory import RolesDirectory
from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
from Products.CPSDirectory.SQLDirectory import SQLDirectory
from Products.CPSDirectory.LDAPBackingDirectory import LDAPBackingDirectory
from Products.CPSDirectory.MetaDirectory import MetaDirectory
from Products.CPSDirectory.StackingDirectory import StackingDirectory
from Products.CPSDirectory.LocalDirectory import LocalDirectory
from Products.CPSDirectory.IndirectDirectory import IndirectDirectory

class MembersDirectoryAddView(BaseAddView):
    """Add view for MembersDirectory."""
    klass = MembersDirectory

class GroupsDirectoryAddView(BaseAddView):
    """Add view for GroupsDirectory."""
    klass = GroupsDirectory

class RolesDirectoryAddView(BaseAddView):
    """Add view for RolesDirectory."""
    klass = RolesDirectory

class ZODBDirectoryAddView(BaseAddView):
    """Add view for ZODBDirectory."""
    klass = ZODBDirectory

class SQLDirectoryAddView(BaseAddView):
    """Add view for SQLDirectory."""
    klass = SQLDirectory

class LDAPBackingDirectoryAddView(BaseAddView):
    """Add view for LDAPBackingDirectory."""
    klass = LDAPBackingDirectory

class MetaDirectoryAddView(BaseAddView):
    """Add view for MetaDirectory."""
    klass = MetaDirectory

class StackingDirectoryAddView(BaseAddView):
    """Add view for StackingDirectory."""
    klass = StackingDirectory

class LocalDirectoryAddView(BaseAddView):
    """Add view for LocalDirectory."""
    klass = LocalDirectory

class IndirectDirectoryAddView(BaseAddView):
    """Add view for IndirectDirectory."""
    klass = IndirectDirectory
