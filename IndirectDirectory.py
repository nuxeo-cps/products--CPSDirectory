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
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter

from Products.CMFCore.utils import getToolByName
from Products.CPSDirectory.BaseDirectory import BaseDirectory

class IndirectDirectory(BaseDirectory):
    """A Directory that just stores ids of entries of another directory.
    """

    meta_type = 'CPS Indirect Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'directory_id', 'type': 'string', 'mode': 'w',
         'label': 'Id of the directory it refers to'},
        {'id': 'object_ids', 'type': 'multiple selection',
         'select_variable': 'listAllpossibleEntries', 'mode': 'w',
         'label': 'Ids of the entries of the other directory'},
        )
    directory_id = ''
    object_ids = []

    def __init__(self, id, **kw):
        BaseDirectory.__init__(self, id, **kw)
        self.directory_id = kw.get('directory_id', '')
        self.object_ids = []

    #
    # API
    #

    security.declarePrivate('listAllpossibleEntries')
    def listAllpossibleEntries(self):
        directory = self._getDirectory()
        return directory.listEntryIds()

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        return list(self.object_ids)

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        ob = self._getContent()
        return ob.listEntryIdsAndTitles()

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        return id in self.object_ids

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        directory = self._getDirectory()
        if directory.hasEntry(id):
            return directory.getEntry(id)
        else:
            return None

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed(entry=entry)
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)
        else:
            directory = self._getDirectory()
            if directory.hasEntry(id):
                object_ids_list = list(self.object_ids)
                object_ids_list.append(id)
                self.object_ids = tuple(object_ids_list)
            else:
                raise KeyError("Entry '%s' does not exist in directory '%s'"
                               % (id, self.directory_id,))

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
        directory = self._getDirectory()
        entries = directory.searchEntries(return_fields, **kw)
        if return_fields is None:
            # If there are no return_fields, you get:
            # ['id1', 'id2', etc.]
            for id in entries:
                if id not in self.object_ids:
                    entries.remove(id)
        else:
            # If there is a return_fields parameter, you get:
            # [('id1', {'field1': value1, 'field2': value2}),
            #  ('id2', {'field1': value3, 'field2': value4}),
            #   etc.
            #  ]
            # return_fields being in this example ('field1', 'field2')
            new_entries = []
            for entry in entries:
                if entry[0] in self.object_ids:
                    new_entries.append(entry)
            entries = new_entries
        return entries

    #
    # Internal
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        directory = self._getDirectory()
        return directory._getAdapters(id, search, **kw)

    security.declarePrivate('_getDirectory')
    def _getDirectory(self):
        dtool = getToolByName(self, 'portal_directories', None)
        directory = getattr(dtool, self.directory_id, None)
        if directory is None:
            raise AttributeError("Directory '%s' does not exist" % self.directory_id)
        else:
            return directory

InitializeClass(IndirectDirectory)
