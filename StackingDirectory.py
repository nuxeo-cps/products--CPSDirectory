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
"""Stacking Directory

A directory that redirects requests to other backing directories.
"""

from zLOG import LOG, DEBUG, WARNING
from types import ListType, TupleType, StringType

from Globals import InitializeClass
from Globals import DTMLFile
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


class StackingDirectory(BaseDirectory):
    """Stacking Directory

    A stacking directory redirects requests to one among several backing
    directories.
    """

    meta_type = 'CPS Stacking Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'backing_dirs', 'type': 'tokens', 'mode': 'w',
         'label': "Backing directories"},
        {'id': 'creation_dir', 'type': 'string', 'mode': 'w',
         'label': "Backing directory for creation"},
        )
    backing_dirs = ()
    creation_dir = ''

    def __init__(self, *args, **kw):
        BaseDirectory.__init__(self, *args, **kw)

    #
    # Internal API
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, **kw):
        """Get the adapters for an entry."""
        dir = self
        schema = self._getSchemas()[0] # XXX must be only one
        adapters = [StackingStorageAdapter(schema, id, dir, **kw)]
        return adapters

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        id_field = self.id_field
        ids = []
        ids_d = {}
        for b_dir in self._getBackingDirs():
            if id_field == b_dir.id_field:
                # Use primary id
                b_ids = b_dir.listEntryIds()
            else:
                # Use secondary id
                # XXX disable acls
                results = b_dir.searchEntries(return_fields=[id_field])
                b_ids = [b_entry[id_field] for primary_id, b_entry in results]
            uids = self._uniqueIdsFromBacking(b_ids, ids_d)
            ids.extend(uids)
        return ids

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        title_field = self.title_field
        if title_field == self.id_field:
            return [(id, id) for id in self.listEntryIds()]
        results = self.searchEntries(return_fields=[title_field])
        return [(id, entry[title_field]) for id, entry in results]

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        id_field = self.id_field
        for b_dir in self._getBackingDirs():
            if id_field == b_dir.id_field:
                # Use primary id
                if b_dir.hasEntry(id):
                    return 1
            else:
                # Use secondary id
                if b_dir.searchEntries(**{id_field: [id]}):
                    return 1
        return 0

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed(entry=entry)
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)
        dir_id = self.creation_dir
        if not dir_id:
            raise ValueError("Creation not allowed (no backing directory)")
        dtool = getToolByName(self, 'portal_directories')
        try:
            b_dir = getattr(dtool, dir_id)
        except AttributeError:
            raise ValueError("No backing directory '%s'" % dir_id)
        b_dir.createEntry(entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed(id=id)
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        id_field = self.id_field
        done = 0
        for b_dir in self._getBackingDirs():
            if id_field == b_dir.id_field:
                # Use primary id
                try:
                    b_dir.deleteEntry(id)
                    done = 1
                except KeyError:
                    pass
            else:
                # Use secondary id
                # XXX don't check acls on search
                b_ids = b_dir.searchEntries(**{id_field: [id]})
                if len(b_ids):
                    if len(b_ids) > 1:
                        LOG('StackingDirectory', WARNING,
                            "Got several entries when asking %s about %s=%s" %
                            (b_dir.getId(), id_field, id))
                    for b_id in b_ids:
                        b_dir.deleteEntry(b_id)
                    done = 1
        if not done:
            raise KeyError(id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory."""
        id_field = self.id_field
        ids_d = {}
        res = []
        for b_dir in self._getBackingDirs():
            b_id_field = b_dir.id_field
            if id_field == b_id_field:
                b_return_fields = return_fields
            else:
                b_return_fields = list(return_fields or ())
                if id_field not in b_return_fields:
                    b_return_fields.append(id_field)

            b_res = b_dir.searchEntries(return_fields=b_return_fields, **kw)

            if return_fields is None:
                if b_return_fields is None:
                    ids = b_res
                else:
                    ids = [b_entry[id_field] for primary_id, b_entry in b_res]
                uids = self._uniqueIdsFromBacking(ids, ids_d)
                res.extend(uids)
            else:
                ures = self._uniqueEntriesFromBacking(b_res, ids_d, b_id_field)
                res.extend(ures)
        return res

    #
    # Internal
    #

    def _getBackingDirs(self):
        """Return the list of backing directories."""
        dtool = getToolByName(self, 'portal_directories')
        res = []
        for dir_id in self.backing_dirs:
            # Get backing dir
            try:
                b_dir = getattr(dtool, dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" % dir_id)
            res.append(b_dir)
        return res

    def _getEntryFromBacking(self, id):
        """Get the entry from the appropriate backing directory.

        Returns the entry and its backing dir.
        """
        id_field = self.id_field
        for b_dir in self._getBackingDirs():
            # Get entry (no acls checked)
            if id_field == b_dir.id_field:
                # Use primary id
                try:
                    entry = b_dir._getEntry(id) # XXX kw?
                except KeyError:
                    continue
            else:
                # Use secondary id
                # XXX don't check acls on search
                entries = b_dir.searchEntries(return_fields=['*'],
                                              **{id_field: [id]})
                if not entries:
                    continue
                if len(entries) > 1:
                    LOG('StackingDirectory', WARNING,
                        "Got several entries when asking %s about %s=%s" %
                        (b_dir.getId(), id_field, id))
                primary_id, entry = entries[0]
            # Back-convert id
            # XXX we cannot do much if there are other dependent fields
            entry[id_field] = id
            return entry, b_dir
        raise KeyError(id)

    def _uniqueIdsFromBacking(self, b_ids, ids_d):
        """Return the back-converted ids from a backing directory.

        Ensures they are unique in dict ids_d.
        """
        ids = []
        for id in b_ids:
            if not ids_d.has_key(id):
                ids_d[id] = None
                ids.append(id)
            else:
                LOG('StackingDirectory', WARNING,
                    "Found duplicate id '%s' when searching %s" %
                    (id, self.getId()))
        return ids

    def _uniqueEntriesFromBacking(self, b_res, ids_d, b_id_field):
        """Return the back-converted entries from a backing directory.

        Ensures their ids are unique in dict ids_d.
        """
        res = []
        id_field = self.id_field
        if id_field == b_id_field:
            for id, b_entry in b_res:
                if not ids_d.has_key(id):
                    ids_d[id] = None
                    res.append((id, b_entry))
                else:
                    LOG('StackingDirectory', WARNING,
                        "Found duplicate id '%s' when searching %s" %
                        (id, self.getId()))
        else:
            for b_id, b_entry in b_res:
                id = b_entry[id_field]
                if not ids_d.has_key(id):
                    ids_d[id] = None
                    res.append((id, b_entry))
                else:
                    LOG('StackingDirectory', WARNING,
                        "Found duplicate id '%s' when searching %s" %
                        (id, self.getId()))
        return res


InitializeClass(StackingDirectory)


class StackingStorageAdapter(BaseStorageAdapter):
    """Stacking Storage Adapter

    This adapter gets and sets data from other backing directories.
    """

    def __init__(self, schema, id, dir, **kw):
        """Create an Adapter for a schema.

        The id passed is the member id. It may be None for creation.
        """
        self._id = id
        self._dir = dir
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
        entry, b_dir = self._dir._getEntryFromBacking(id)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)

        old_entry, b_dir = self._dir._getEntryFromBacking(self._id)

        # XXX Note: if we attempt to change the backing id here, we get
        # a KeyError. Unless an entry with the new backing id already exists,
        # in which case, it would be overwritten...
        # An explicit test would be better.
        b_dir.editEntry(data)

InitializeClass(StackingStorageAdapter)
