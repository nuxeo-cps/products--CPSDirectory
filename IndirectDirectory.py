# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Anahide Tchertchian <at@nuxeo.com>
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
"""IndirectDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from types import TupleType, StringType

from Products.CMFCore.utils import getToolByName
from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

class IndirectDirectory(BaseDirectory):
    """A Directory that just stores ids of entries of other directories.
    """

    meta_type = 'CPS Indirect Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'directory_ids', 'type': 'tokens', 'mode': 'w',
         'label': 'Ids of the directories it refers to'},
        {'id': 'object_ids', 'type': 'multiple selection',
         'select_variable': 'listAllPossibleEntriesIds', 'mode': 'w',
         'label': 'Ids of the entries of the others directories'},
        )
    # list of directory ids
    directory_ids = []
    # list of strings directory_id/entry_id using '/' as a special character
    object_ids = []

    def __init__(self, id, **kw):
        BaseDirectory.__init__(self, id, **kw)

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        return list(self.object_ids)

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        # Default dummy implementation.
        # To be implemented
        return [(id, id) for id in self.listEntryIds()]

    security.declarePrivate('listAllPossibleEntriesIds')
    def listAllPossibleEntriesIds(self):
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            res_to_append = [self._makeId(directory_id,x) for x in directory.listEntryIds()]
            res.extend(res_to_append)
        return res

    security.declarePrivate('listAllPossibleEntriesIdsAndTitles')
    def listAllPossibleEntriesIdsAndTitles(self):
        # Default dummy implementation.
        # To be implemented
        return [(id, id) for id in self.listAllPossibleEntriesIds()]

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        return id in self.listEntryIds()

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        if not id:
            return None
        else:
            directory_id = self._getDirectoryIdForId(id)
            entry_id = self._getEntryIdForId(id)
            directory = self._getDirectory(directory_id)
            if not directory.hasEntry(entry_id):
                return None
            else:
                entry = directory.getEntry(entry_id)
                # giving to entry the good id...
                id = entry[directory.id_field]
                entry[directory.id_field] = self._makeId(directory_id, id)
                return entry

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed(entry=entry)
        if entry is not None:
            # entry is supposed to have the good id already...
            id = entry[self.id_field]
            directory_id = self._getDirectoryIdForId(id)
            entry_id = self._getEntryIdForId(id)
            if self.hasEntry(id):
                raise KeyError("Entry '%s' already exists" % id)
            else:
                directory = self._getDirectory(directory_id)
                if directory.hasEntry(entry_id):
                    object_ids_list = list(self.object_ids)
                    object_ids_list.append(id)
                    self.object_ids = tuple(object_ids_list)
                else:
                    raise KeyError("Entry '%s' does not exist in directory '%s'"
                                   % (entry_id, directory_id,))

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed(id=id)
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist !" % id)
        object_ids_list = list(self.object_ids)
        object_ids_list.remove(id)
        self.object_ids = tuple(object_ids_list)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.
        """
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            real_entries = directory.searchEntries(return_fields, **kw)
            # filter entries returned from the search on the
            # real directory
            if return_fields is None:
                # If there are no return_fields, you get:
                # ['id1', 'id2', etc.]
                entries = [self._makeId(directory_id, x) for x in real_entries]
                new_entries = []
                for id in entries:
                    if id in self.object_ids:
                        new_entries.append(id)
                entries = new_entries
            else:
                # If there is a return_fields parameter, you get:
                # [('id1', {'field1': value1, 'field2': value2}),
                #  ('id2', {'field1': value3, 'field2': value4}),
                #   etc.
                #  ]
                # return_fields being in this example ('field1', 'field2')
                entries = [(self._makeId(directory_id, x[0]), x[1]) for x in real_entries]
                new_entries = []
                for entry in entries:
                    if entry[0] in self.object_ids:
                        new_entries.append(entry)
                entries = new_entries
            res.extend(entries)
        return res

    security.declarePublic('searchPossibleEntries')
    def searchPossibleEntries(self, return_fields=None, **kw):
        """Search for possible entries in the directories.
        """
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            real_entries = directory.searchEntries(return_fields, **kw)
            # filter entries returned from the search on the
            # real directory
            if return_fields is None:
                # If there are no return_fields, you get:
                # ['id1', 'id2', etc.]
                entries = [self._makeId(directory_id, x) for x in real_entries]
            else:
                # If there is a return_fields parameter, you get:
                # [('id1', {'field1': value1, 'field2': value2}),
                #  ('id2', {'field1': value3, 'field2': value4}),
                #   etc.
                #  ]
                # return_fields being in this example ('field1', 'field2')
                entries = [(self._makeId(directory_id, x[0]), x[1]) for x in real_entries]
            res.extend(entries)
        return res


    #
    # Internal
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        if id is not None:
            entry_id = self._getEntryIdForId(id)
            directory_id = self._getDirectoryIdForId(id)
        else:
            entry_id = None
            try:
                directory_id = self.directory_ids[0]
            except IndexError:
                return []
        directory = self._getDirectory(directory_id)
        original_adapters = directory._getAdapters(entry_id, search, **kw)
        adapters = [IndirectStorageAdapter(adapter.getSchema(),
                                           id=entry_id,
                                           dir=directory,
                                           indirect_id=id,
                                           adapter=adapter,
                                           **kw)
                    for adapter in original_adapters]
        return adapters

    security.declarePrivate('_getDirectory')
    def _getDirectory(self, directory_id):
        if directory_id not in self.directory_ids:
            raise AttributeError("Directory '%s' is not allowed" % directory_id)
        dtool = getToolByName(self, 'portal_directories', None)
        directory = getattr(dtool, directory_id, None)
        if directory is None:
            raise AttributeError("Directory '%s' does not exist" % directory_id)
        else:
            return directory

    security.declarePrivate('_makeId')
    def _makeId(self, directory_id, entry_id):
        return directory_id+'/'+entry_id

    security.declarePrivate('_getDirectoryIdForId')
    def _getEntryIdForId(self, id):
        try:
            res = id.split('/')[1]
        except IndexError:
            res = None
        return res

    security.declarePrivate('_getDirectoryIdForId')
    def _getDirectoryIdForId(self, id):
        try:
            res = id.split('/')[0]
        except IndexError:
            res = None
        return res

    security.declarePrivate('_getDirectoryIdForId')
    def _getEntryIdForId(self, id):
        try:
            res = id.split('/')[1]
        except IndexError:
            res = None
        return res

InitializeClass(IndirectDirectory)


class IndirectStorageAdapter(BaseStorageAdapter):
    """Indirect Storage Adapter

    This adapter gets and sets data from the user folder and the member
    data.
    """

    def __init__(self, schema, id, dir, indirect_id, adapter, **kw):
        """Create an Adapter for a schema.

        The id passed is the member id within the directory.
        indirect_id is in fact 'directory/id'.
        """
        self._id = id
        self._dir = dir
        self._indirect_id = indirect_id
        self._adapter = adapter
        BaseStorageAdapter.__init__(self, schema, **kw)

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        if self._id is None:
            data = self.getDefaultData()
        else:
            data = self._adapter.getData()
            dir = self._dir
            if data.has_key(dir.id_field):
                data[dir.id_field] = self._indirect_id
        return data

InitializeClass(IndirectStorageAdapter)
