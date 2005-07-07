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

import re

def match_pattern(pattern, value):
    """Tells whether value matches pattern.

    Returns 1 if pattern is a substring of value, considering that the '*'
    character matches any character string.
    '*' is the only special character accepted.
    """
    pattern = pattern.lower()
    value = value.lower()
    if pattern.find('*') != -1:
        re_pattern = re.compile(pattern.replace('*', '.*'), re.DOTALL)
        if re_pattern.search(value) is None:
            res = 0
        else:
            res = 1
    else:
        if value.find(pattern) != -1:
            res = 1
        else:
            res = 0
    return res


class IndirectDirectory(BaseDirectory):
    """A Directory that just stores ids of entries of other directories.

    An id for an indirect directory is the string of characters
    <directory>/<id> where <directory> is the id of the directory holding the
    real entry, and <id> is the id of the real entry within this directory.
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
    object_ids = ()

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
        title_field = self.title_field
        if self.id_field == title_field:
            res = [(id, id) for id in self.listEntryIds()]
        else:
            res = []
            # Get all the fields that title may depend on
            field_ids_d = {title_field: None}
            schema = self._getSchemas()[0]
            dep_ids = schema[title_field].read_process_dependent_fields
            for dep_id in dep_ids:
                field_ids_d[dep_id] = None
            # id field is already in dependant fields
            if self.id_field in field_ids_d:
                del field_ids_d[self.id_field]
            for id in self.listEntryIds():
                entry_id = self._getEntryIdForId(id)
                directory_id = self._getDirectoryIdForId(id)
                directory = self._getDirectory(directory_id)
                adapter = IndirectStorageAdapter(schema,
                                                 id=entry_id,
                                                 dir=directory,
                                                 indirect_id=id,
                                                 **field_ids_d)
                entry = adapter.getData()
                adapter.finalizeDefaults(entry)
                res.append((id, entry[title_field]))
        return res

    security.declarePrivate('listAllPossibleEntriesIds')
    def listAllPossibleEntriesIds(self):
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            res_to_append = [self._makeId(directory_id, x)
                             for x in directory.listEntryIds()]
            res.extend(res_to_append)
        return res

    security.declarePrivate('listAllPossibleEntriesIdsAndTitles')
    def listAllPossibleEntriesIdsAndTitles(self):
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            res_to_append = [(self._makeId(directory_id, x[0]), x[1])
                             for x in directory.listEntryIdsAndTitles()]
            res.extend(res_to_append)
        return res

    security.declarePrivate('_hasEntry')
    def _hasEntry(self, id):
        """Does the directory have a given entry?"""
        # XXX should use base class implementation
        return id in self.listEntryIds()

    security.declarePrivate('_createEntry')
    def _createEntry(self, entry):
        """Create an entry in the directory.

        Create an entry consists in adding the indirect id into the list of
        objects kept as an attribute in the indirect directory. There is no
        edition to be done on the entry.
        """
        if entry is not None:
            # entry is supposed to have the good id already...
            id = entry[self.id_field]
            directory_id = self._getDirectoryIdForId(id)
            entry_id = self._getEntryIdForId(id)
            if self._hasEntry(id):
                raise KeyError("Entry '%s' already exists" % id)
            else:
                directory = self._getDirectory(directory_id)
                if directory._hasEntry(entry_id):
                    self.object_ids = self.object_ids + (id,)
                else:
                    raise KeyError("Entry '%s' does not exist in directory '%s'"
                                   % (entry_id, directory_id,))

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory.

        Deleting an entry from the indirect directory consists in removing the
        indirect id from the list of references.
        """
        self.checkDeleteEntryAllowed(id=id)
        if not self._hasEntry(id):
            raise KeyError("Entry '%s' does not exist !" % id)
        object_ids_list = list(self.object_ids)
        object_ids_list.remove(id)
        self.object_ids = tuple(object_ids_list)

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the indirect directory.

        Return entries matching the following criteria:
        - a reference towards the entry is kept in the indirect directory
        - the entry matches the search criteria as if the search was made
          within the directory that actually stores it.
        """
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            id_field = directory.id_field
            indirect_ids = [self._getEntryIdForId(x) for x in self.object_ids
                            if self._getDirectoryIdForId(x) == directory_id]
            # add kw to the search made on directory so that only
            # objects already in indirect are searched
            new_kw = kw.copy()
            kw_id = kw.get(id_field, '')
            if kw_id:
                indirect_ids = [x for x in indirect_ids if match_pattern(kw_id, x)]
            if not indirect_ids:
                entries = []
            else:
                new_kw[id_field] = indirect_ids
                real_entries = directory._searchEntries(return_fields, **new_kw)
                entries = self.formatSearchResults(return_fields,
                                                   directory_id,
                                                   real_entries)
            res.extend(entries)
        return res

    security.declarePublic('searchPossibleEntries')
    def searchPossibleEntries(self, return_fields=None, **kw):
        """Search for possible entries in the directories.

        Return entries matching the search criteria, whether a reference
        towards each entry is kept in the indirect directory or not. This
        method is useful when creating new entries in the indirect directory.
        """
        res = []
        for directory_id in self.directory_ids:
            directory = self._getDirectory(directory_id)
            real_entries = directory.searchEntries(return_fields, **kw)
            # do not filter entries returned from the search on the real
            # directory
            entries = self.formatSearchResults(return_fields,
                                               directory_id,
                                               real_entries)
            res.extend(entries)
        return res

    security.declarePublic('getSearchResults')
    def formatSearchResults(self, return_fields, directory_id, results):
        """ Format search results according.

        Search results are formatted according to the return_fields parameter,
        and identifiers are changed according to the format used in indirect
        directories.
        """
        if return_fields is None:
            # If there are no return_fields, you get:
            # ['id1', 'id2', etc.]
            res = [self._makeId(directory_id, x) for x in results]
        else:
            # If there is a return_fields parameter, you get:
            # [('id1', {'field1': value1, 'field2': value2}),
            #  ('id2', {'field1': value3, 'field2': value4}),
            #   etc.
            #  ]
            # return_fields being in this example ('field1', 'field2')
            res = [(self._makeId(directory_id, x[0]), x[1]) for x in results]
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
            directory = self._getDirectory(directory_id)
        else:
            entry_id = None
            directory = None

        adapters = [IndirectStorageAdapter(schema,
                                           id=entry_id,
                                           dir=directory,
                                           indirect_id=id,
                                           **kw)
                    for schema in self._getSchemas(search=search)]
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
    def _getDirectoryIdForId(self, id):
        try:
            res = id.split('/')[0]
        except IndexError:
            res = None
        return res

    security.declarePrivate('_getEntryIdForId')
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

    def __init__(self, schema, id, dir, indirect_id, **kw):
        """Create an Adapter for a schema.

        The id passed is the member id within the directory.
        indirect_id is in fact 'directory/id'.
        """
        self._id = id
        self._dir = dir
        self._indirect_id = indirect_id
        BaseStorageAdapter.__init__(self, schema, **kw)

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default data if the id is None.
        The mapping comes from the actual entry kept in the directory it refers
        to, and this mapping is filtered using fields defined in the indirect
        directory schemas.
        The id value is changed so that the id is the indirect id, and not the
        id of the entry within its directory (keeping the information of the
        directory that actually holds the entry).
        """
        if self._id is None:
            data = self.getDefaultData()
        else:
            dir = self._dir
            old_data = dir.getEntry(self._id, default=None)
            if old_data is None:
                # KeyError will be catched by getEntry if
                # a default value can be provided
                raise KeyError
            else:
                data = self.getDefaultData()
                # filter with fields in indirect schema
                for field in data.keys():
                    if old_data.has_key(field):
                        data[field] = old_data[field]
                if data.has_key(dir.id_field):
                    data[dir.id_field] = self._indirect_id
        return data

InitializeClass(IndirectStorageAdapter)
