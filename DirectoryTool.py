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

try:
    set
except NameError:
    # python 2.3 compat
    from sets import Set as set


from zLOG import LOG, DEBUG

from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from AccessControl.PermissionRole import PermissionRole

from OFS.Folder import Folder

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal

from Products.CPSDirectory.BaseDirectory import BaseDirectory

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

    security.declarePrivate('_crossGetList')
    def _crossGetList(self, dir_id, field_id, value):
        """Return the list of entry ids of 'dir_id' such that 'value' is in
        'field_id'

        'field_id' is assumed to be a String List Field of 'dir_id'

        This method is used in the computed 'members' field of the groups
        directory's schema to list all members that belong to some group.
        """
        dir = self[dir_id]
        stool = getToolByName(self, 'portal_schemas')
        if field_id not in stool[dir.schema].fields:
            raise KeyError("%s not in %s's fields" % (field_id, dir_id))
        return dir._searchEntries(**{field_id: [value]})

    security.declarePrivate('_crossSetList')
    def _crossSetList(self, dir_id, field_id, value, entry_ids):
        """Update the field 'field_id' of 'dir_id' so that only entries of
        'dir_id' occuring in 'entry_ids' have 'value' in 'field_id'

        'field_id' is assumed to be a String List Field of 'dir_id'

        This method is used in the computed 'members' field of the groups
        directory's schema to write the list of members that belong to some
        group.
        """
        dir = self[dir_id]
        entry_ids = set(entry_ids)
        with_value = dir._searchEntries(return_fields=[field_id],
                                        **{field_id: [value]})
        ids_with_value = [id for id, e in with_value]
        for id, entry in with_value:
            if id in entry_ids:
                continue
            # Remove the value from the field
            values = entry[field_id]
            if value not in values:
                # Sanity check, in case the search had weird semantics
                continue
            values.remove(value)
            new_entry = {
                dir.id_field: id,
                field_id: values,
                }
            entry = dir._editEntry(new_entry)
        for id in entry_ids.difference(ids_with_value):
            entry = dir._getEntryKW(id, field_ids=[field_id])
            # Add the value to the field
            values = entry[field_id]
            if value in values:
                # Sanity check, in case the search had weird semantics
                continue
            values.append(value)
            new_entry = {
                dir.id_field: id,
                field_id: values,
                }
            entry = dir._editEntry(new_entry) 

    #
    # ZMI
    #

    def all_meta_types(self):
        # Stripping is done to be able to pass a type in the URL.
        meta_types = [
            {'name': dt,
             # _verifyObjectPaste needs this to be traversable
             # to a real object.
             'action': 'manage_addForm_' + dt.replace(' ', ''),
             'permission': ManagePortal}
            for dt in DirectoryTypeRegistry.listTypes()]
        for info in Folder.all_meta_types(self):
            name = info['name']
            if (name.startswith('Z') and
                name.endswith('Database Connection')):
                meta_types.append(info)
            elif name.endswith('RAM Cache Manager'):
                meta_types.append(info)
        return meta_types

    security.declareProtected(ManagePortal, 'manage_addCPSDirectoryForm')
    manage_addCPSDirectoryForm = DTMLFile('zmi/directory_addform', globals())

    security.declareProtected(ManagePortal, 'manage_addCPSDirectory')
    def manage_addCPSDirectory(self, id, meta_type, REQUEST=None, **kw):
        """Add a directory, called from the ZMI."""
        container = self
        cls = DirectoryTypeRegistry.getType(meta_type)
        ob = cls(id, **kw)
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
        # Monkey-patch a new factory class into the tool
        name = 'manage_addForm_' + mt
        def manage_add(self, REQUEST=None, mt=mt):
            """Add some meta_type directory."""
            return self.manage_addCPSDirectoryForm(mt=mt, REQUEST=REQUEST)
        perm = PermissionRole(ManagePortal)
        setattr(DirectoryTool, name, manage_add)
        setattr(DirectoryTool, name+'__roles__', perm)

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
