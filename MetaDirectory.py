# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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
"""Meta Directory

A directory redirects requests to other backing directories.
"""

from zLOG import LOG, DEBUG, WARNING
from copy import deepcopy

from Globals import InitializeClass
from Globals import DTMLFile
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = [] # XXX used?


class DirectoryMapping:
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self, dir_id,
                 id_conv=None, field_rename=None, field_ignore=None):
        self.dir_id = dir_id
        self.id_conv = id_conv
        self.field_rename = field_rename or {}
        self.field_ignore = field_ignore or ()

InitializeClass(DirectoryMapping)


class MetaDirectory(BaseDirectory):
    """Meta Directory

    A directory redirects requests to other backing directories.
    """

    meta_type = 'CPS Meta Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'backing_dir_ids', 'type': 'tokens', 'mode': 'w',
         'label': 'Backing directories'},
        )
    backing_dir_ids = ()

    def __init__(self, *args, **kw):
        BaseDirectory.__init__(self, *args, **kw)
        self.backing_dirs_mappings = {}

    #
    # ZMI
    #

    manage_options = (
        BaseDirectory.manage_options[:1] + (
        {'label': 'Mappings', 'action': 'manage_metadirMappings'},
        ) + BaseDirectory.manage_options[1:]
        )

    security.declareProtected(ManagePortal, 'manage_metadirMappings')
    manage_metadirMappings = DTMLFile('zmi/metadir_mappings', globals())


    #
    # Management API
    #

    security.declareProtected(ManagePortal, 'getBackingDirectoriesMappings')
    def getBackingDirectoriesMappings(self):
        """Get the list of backing directories and their mappings."""
        return [DirectoryMapping('dirfoo',
                                 id_conv=None,
                                 field_rename={},
                                 field_ignore=('pasglop',),
                                 ),
                DirectoryMapping('dirbar',
                                 id_conv=None,
                                 field_rename={'mail': 'email'}, # back:meta
                                 field_ignore=(),
                                 ),
                ]

    #
    # Internal API
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, **kw):
        """Get the adapters for an entry."""
        dir = self
        schema = self._getSchemas()[0] # XXX must be only one
        adapters = [MetaStorageAdapter(schema, id, dir, **kw)]
        return adapters

    #
    # API
    #

    security.declarePrivate('_getFirstDirectory')
    def _getFirstDirectory(self):
        """Get the first directory."""
        # XXX later: first directory that has no id conversion
        mappings = self.getBackingDirectoriesMappings()
        if not mappings:
            return None
        dir_id = mappings[0].dir_id
        dtool = getToolByName(self, 'portal_directories')
        try:
            dir = getattr(dtool, dir_id)
        except AttributeError:
            raise ValueError("No backing directory '%s'" % dir_id)
        return dir

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        # We get the ids from the first directory.
        # XXX later: first directory that has no id conversion
        dir = self._getFirstDirectory()
        if dir is None:
            return []
        return dir.listEntryIds()

    #def listEntryIdsAndTitles(self): XXX

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        dir = self._getFirstDirectory()
        if dir is None:
            return 0
        return dir.hasEntry(id)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        id = entry[self.id_field]
        self.checkCreateEntryAllowed(id=id)
        if self.hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)

        # Fetch a dm with default values
        dm = self._getDataModel(None, check_acls=0, do_create=1)
        # Set the values
        for key in dm.keys():
            if not entry.has_key(key):
                continue
            dm[key] = entry[key]
        # Now set datamodel's id
        # XXX Should use better API
        for adapter in dm._adapters:
            adapter.setContextObject(id)
        dm._commit()

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed()
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        dtool = getToolByName(self, 'portal_directories')
        for mapping in self.getBackingDirectoriesMappings():
            # Get backing dir
            try:
                dir = getattr(dtool, mapping.dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" %
                                 mapping.dir_id)
            # Get id XXX maybe convert
            b_id = id
            dir.deleteEntry(b_id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        raise NotImplementedError
        #1. build queries for each backing dir
        #2. find in what order to do search
        #3. do searches
        #4. intersect results
        #5. merge entries from each backing dir


    #
    # Internal
    #

    def _getEntryFromBacking(self, entry_id, field_ids):
        """Compute an entry from the backing directories."""
        dtool = getToolByName(self, 'portal_directories')
        entry = {self.id_field: entry_id}
        for mapping in self.getBackingDirectoriesMappings():
            # Get backing dir
            try:
                dir = getattr(dtool, mapping.dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" %
                                 mapping.dir_id)
            # Get id XXX maybe convert
            b_id = entry_id
            # Get field ids we want
            b_fids = []
            for schema in dir._getSchemas():     # XXX
                for b_fid in schema.keys(): # XXX need API for this
                    if b_fid == dir.id_field:
                        # Ignore id
                        continue
                    if b_fid in mapping.field_ignore:
                        # Ignore fields ignored by mapping
                        continue
                    fid = mapping.field_rename.get(b_fid, b_fid)
                    if fid not in field_ids:
                        # Ignore fields unwanted in arguments
                        continue
                    b_fids.append(b_fid)
            # Get entry (no acls checked)
            if not b_fids:
                continue
            b_entry = dir._getEntry(b_id, fields_ids=b_fids)
            # Keep what we need in entry
            for b_fid in b_fids:
                # Do renaming
                fid = mapping.field_rename.get(b_fid, b_fid)
                entry[fid] = b_entry[b_fid]
        return entry

InitializeClass(MetaDirectory)


class MetaStorageAdapter(BaseStorageAdapter):
    """Meta Storage Adapter

    This adapter gets and sets data from other backing directories.
    """

    def __init__(self, schema, id, dir, **kw):
        """Create an Adapter for a schema.

        The id passed is the member id. It may be None for creation.
        """
        self._id = id
        self._dir = dir
        self._do_create = kw.get('do_create', 0)
        BaseStorageAdapter.__init__(self, schema, **kw)

    def setContextObject(self, context):
        """Set a new underlying context for this adapter."""
        self._id = context

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        if id is None:
            # Creation.
            return self.getDefaultData()
        # Compute entry so that it is passed as kw to _getFieldData.
        field_ids = [field_id for field_id, field in self.getFieldItems()]

        entry = self._dir._getEntryFromBacking(id, field_ids)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)
        dir = self._dir
        entry_id = self._id

        # Do we assume we want to write all fields ?

        dtool = getToolByName(dir, 'portal_directories')

        for mapping in dir.getBackingDirectoriesMappings():
            # Get backing dir
            try:
                dir = getattr(dtool, mapping.dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" %
                                 mapping.dir_id)
            # Get id XXX maybe convert
            b_id = entry_id

            # Build backing entry
            b_entry = {}
            for schema in dir._getSchemas():     # XXX
                for b_fid in schema.keys(): # XXX need API for this
                    if b_fid == dir.id_field:
                        # Ignore id, already done.
                        continue
                    if b_fid in mapping.field_ignore:
                        # Ignore fields ignored by mapping
                        continue
                    fid = mapping.field_rename.get(b_fid, b_fid)
                    if not data.has_key(fid):
                        # Skip fields missing in data
                        continue
                    b_entry[b_fid] = data[fid]
            # Build id last to be sure it's there
            b_entry[dir.id_field] = b_id

            # Write or create to backing dir
            if self._do_create:
                dir.createEntry(b_entry)
            else:
                dir.editEntry(b_entry)

InitializeClass(MetaStorageAdapter)
