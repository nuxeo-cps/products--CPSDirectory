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


class StackingDirectory(BaseDirectory):
    """Stacking Directory

    A stacking directory redirects requests to one among several backing
    directories.
    """

    meta_type = 'CPS Stacking Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'creation_dir_expr', 'type': 'string', 'mode': 'w',
         'label': "Directory used for creation (TALES)"},
        )
    creation_dir_expr = ''

    creation_dir_expr_c = None

    _properties_post_process_tales = (
        ('creation_dir_expr', 'creation_dir_expr_c'),
        )

    def __init__(self, *args, **kw):
        BaseDirectory.__init__(self, *args, **kw)

    #
    # ZMI
    #

    manage_options = (
        BaseDirectory.manage_options[:1] + (
        {'label': 'Backing Directories', 'action': 'manage_stackingDirs'},
        ) + BaseDirectory.manage_options[1:]
        )

    security.declareProtected(ManagePortal, 'manage_stackingDirs')
    manage_stackingDirs = DTMLFile('zmi/stackingdir_dirs', globals())

    #
    # Management API
    #

    security.declareProtected(ManagePortal, 'getBackingDirectories')
    def getBackingDirectories(self):
        """Get the list of backing directories and their info."""
        return self.backing_dir_infos
        #return (
        #    # dir_id, style, prefix/suffix, strip
        #    ('dirfoo', 'prefix', 'a_', 0),
        #    ('dirbar', 'suffix', '_b', 1),
        #    ('dirbaz', 'none', None, 0),
        #    )

    security.declareProtected(ManagePortal, 'setBackingDirectories')
    def setBackingDirectories(self, backing_dir_infos):
        """Set the list of backing directories and their info."""
        infos = []
        for dir_id, style, fix, strip in backing_dir_infos:
            if style == 'none':
                if fix or strip:
                    raise ValueError("Bad info for dir '%s'" % dir_id)
            elif style in ('prefix', 'suffix'):
                if not fix:
                    raise ValueError("Bad info for dir '%s': needs a %s"
                                     % (dir_id, style))
            else:
                raise ValueError("Bad info for dir '%s': unknown style '%s'"
                                 % (dir_id, style))
            infos.append((str(dir_id),
                          style,
                          fix or None,
                          not not strip))
        self.backing_dir_infos = tuple(infos)

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
        dtool = getToolByName(self, 'portal_directories')
        ids = []
        ids_d = {}
        for dir_id, style, fix, strip in self.getBackingDirectories():
            # Get backing dir
            try:
                b_dir = getattr(dtool, dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" % dir_id)
            # Find and convert ids
            b_ids = b_dir.listEntryIds()
            if style == 'none':
                for id in b_ids:
                    if not ids_d.has_key(id):
                        ids.append(id)
                        ids_d[id] = None
                    # XXX else warn
            elif style == 'prefix':
                if strip:
                    for b_id in b_ids:
                        id = fix + b_id
                        if not ids_d.has_key(id):
                            ids.append(id)
                            ids_d[id] = None
                        # XXX else warn
                else:
                    # Only keep ids that have correct prefix
                    for b_id in b_ids:
                        if not b_id.startswith(fix):
                            continue
                        id = b_id
                        if not ids_d.has_key(id):
                            ids.append(id)
                            ids_d[id] = None
                        # XXX else warn
            elif style == 'suffix': # and strip
                if strip:
                    for b_id in b_ids:
                        id = b_id + fix
                        if not ids_d.has_key(id):
                            ids.append(id)
                            ids_d[id] = None
                        # XXX else warn
                else:
                    # Only keep ids that have correct suffix
                    for b_id in b_ids:
                        if not b_id.endswith(fix):
                            continue
                        id = b_id
                        if not ids_d.has_key(id):
                            ids.append(id)
                            ids_d[id] = None
                        # XXX else warn
            else:
                raise ValueError(style)
        return ids

    #def listEntryIdsAndTitles(self): XXX

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        dtool = getToolByName(self, 'portal_directories')
        for dir_id, style, fix, strip in self.getBackingDirectories():
            # Get backing dir
            try:
                b_dir = getattr(dtool, dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" % dir_id)
            # Get potential backing id
            b_id = self._getBackingId(id, style, fix, strip)
            if b_id is None:
                continue
            # Test presence
            if b_dir.hasEntry(b_id):
                return 1
        return 0

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        id = entry[self.id_field]
        self.checkCreateEntryAllowed(id=id)
        if self.hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)
        b_dir, b_id = self._getBackingForId(id)
        b_entry = entry.copy()
        b_entry[b_dir.id_field] = b_id
        b_dir.createEntry(b_entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed()
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        b_dir, b_id = self._getBackingForId(id)
        b_dir.deleteEntry(b_id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        raise NotImplementedError
        #1. build queries for each backing dir
        #3. do searches
        #4. union results


    #
    # Internal
    #

    def _getBackingId(self, id, style, fix, strip):
        """Get backing id from info.

        Returns None if cannot exist.
        """
        if style == 'none':
            b_id = id
        elif style == 'prefix':
            if not id.startswith(fix):
                b_id = None
            elif strip:
                b_id = id[len(fix):]
            else:
                b_id = id
        elif style == 'suffix':
            if not id.endswith(fix):
                b_id = None
            elif strip:
                b_id = id[:-len(fix)]
            else:
                b_id = id
        else:
            raise ValueError(style)
        return b_id

    def _getEntryFromBacking(self, id):
        """Get the entry from the appropriate backing directory."""
        dtool = getToolByName(self, 'portal_directories')
        for dir_id, style, fix, strip in self.getBackingDirectories():
            # Get backing dir
            try:
                b_dir = getattr(dtool, dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" % dir_id)
            # Get id
            b_id = self._getBackingId(id, style, fix, strip)
            if b_id is None:
                continue
            # Get entry (no acls checked)
            try:
                entry = b_dir._getEntry(b_id) # XXX kw?
            except KeyError:
                continue
            # Back-convert id
            entry[b_dir.id_field] = id
            return entry
        raise KeyError(id)

    def _getBackingForId(self, id):
        """Find the backing directory into which an entry goes.

        Returns a dir and the backing entry id.
        """
        dtool = getToolByName(self, 'portal_directories')
        for dir_id, style, fix, strip in self.getBackingDirectories():
            # Get backing dir
            try:
                b_dir = getattr(dtool, dir_id)
            except AttributeError:
                raise ValueError("No backing directory '%s'" % dir_id)
            # Get id
            b_id = self._getBackingId(id, style, fix, strip)
            if b_id is None:
                continue
            return b_dir, b_id
        raise KeyError(id)

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
        entry = self._dir._getEntryFromBacking(id)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)
        dir = self._dir
        id = self._id

        b_dir, b_id = dir._getBackingForId(id)
        data[b_dir.id_field] = b_id
        b_dir.editEntry(data)

InitializeClass(StackingStorageAdapter)
