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

from Globals import InitializeClass
from Globals import DTMLFile
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed


class MetaDirectory(BaseDirectory):
    """Meta Directory

    A directory redirects requests to other backing directories.
    """

    meta_type = 'CPS Meta Directory'

    security = ClassSecurityInfo()

    backing_dir_infos = ()

    def __init__(self, *args, **kw):
        BaseDirectory.__init__(self, *args, **kw)

    #
    # ZMI
    #

    manage_options = (
        BaseDirectory.manage_options[:1] + (
        {'label': 'Backings', 'action': 'manage_editBackings'},
        ) + BaseDirectory.manage_options[1:]
        )

    security.declareProtected(ManagePortal, 'manage_editBackings')
    manage_editBackings = DTMLFile('zmi/metadir_backings', globals())

    security.declareProtected(ManagePortal, 'manage_changeBacking')
    def manage_changeBacking(self, dir_id, field_ignore, field_renames,
                             delete=0, REQUEST=None):
        """Change mappings from ZMI."""
        infos = self.getBackingDirectories(no_dir=1)
        new_infos = []
        msg = 'Changed.'
        for info in infos:
            if info['dir_id'] != dir_id:
                new_infos.append(info)
                continue
            if delete:
                msg = 'Deleted.'
                continue
            info['field_ignore'] = field_ignore
            field_rename = {}
            for d in field_renames:
                field_rename[d['b_id']] = d['id']
            info['field_rename'] = field_rename
            new_infos.append(info)
        self.setBackingDirectories(new_infos)
        if REQUEST is not None:
            args = 'manage_tabs_message='+msg
            REQUEST.RESPONSE.redirect(self.absolute_url()+
                                      '/manage_editBackings?'+args)

    security.declareProtected(ManagePortal, 'manage_addBacking')
    def manage_addBacking(self, dir_id, field_ignore, field_renames,
                          REQUEST=None):
        """Change mappings from ZMI."""
        infos = self.getBackingDirectories(no_dir=1)
        field_rename = {}
        for d in field_renames:
            field_rename[d['b_id']] = d['id']
        infos.append({'dir_id': dir_id.strip(),
                      'field_ignore': field_ignore,
                      'field_rename': field_rename,
                      })
        self.setBackingDirectories(infos)
        if REQUEST is not None:
            args = 'manage_tabs_message=Added.'
            REQUEST.RESPONSE.redirect(self.absolute_url()+
                                      '/manage_editBackings?'+args)

    #
    # Management API
    #

    security.declareProtected(ManagePortal, 'getBackingDirectories')
    def getBackingDirectories(self, no_dir=0):
        """Get the list of backing directories and their infos.

        Returns a sequence of dicts with keys dir, dir_id, id_conv, ...

        If no_dir, do not attempt to add the dir object.
        """
        dtool = getToolByName(self, 'portal_directories')
        infos = []
        for b_info in self.backing_dir_infos:
            info = b_info.copy()
            if not no_dir:
                dir_id = b_info['dir_id']
                try:
                    dir = getattr(dtool, dir_id)
                except AttributeError:
                    raise ValueError("No backing directory '%s'" % dir_id)
                info['dir'] = dir
            infos.append(info)
        return infos

    security.declareProtected(ManagePortal, 'setBackingDirectories')
    def setBackingDirectories(self, infos):
        """Set the list of backing directories and their infos.

        Infos is a sequence of dicts with keys dir_id, id_conv,
        field_rename, field_ignore.
        """
        backing_dir_infos = []
        for info in infos:
            renames = info.get('field_rename') or {}
            field_ignore = info.get('field_ignore')
            field_rename = {}
            field_rename_back = {}
            for back, meta in renames.items():
                back = back.strip()
                meta = meta.strip()
                if not back or not meta or back == meta:
                    continue
                if field_rename.has_key(back):
                    raise ValueError("Field id '%s' is used twice" % back)
                if field_rename_back.has_key(meta):
                    raise ValueError("Field id '%s' is renamed twice" % meta)
                field_rename[back] = meta
                field_rename_back[meta] = back
            backing_dir_infos.append(
                {'dir_id': info['dir_id'],
                 'id_conv': info.get('id_conv'),
                 'field_rename': field_rename.copy(),
                 'field_rename_back': field_rename_back,
                 'field_ignore': field_ignore and tuple(field_ignore) or (),
                 })
        self.backing_dir_infos = tuple(backing_dir_infos)

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
        infos = self.getBackingDirectories()
        if not infos:
            return None
        return infos[0]['dir']

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        # We get the ids from the first directory.
        # XXX later: first directory that has no id conversion
        dir = self._getFirstDirectory()
        if dir is None:
            return []
        return dir.listEntryIds()

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
        dir = self._getFirstDirectory()
        if dir is None:
            return 0
        return dir.hasEntry(id)

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.

        Asks the backing directories, one of them must be authenticating.
        """
        for b_dir in self._getBackingDirs():
            if b_dir.isAuthenticating():
                return 1
        return 0

    security.declarePrivate('getEntryAuthenticated')
    def getEntryAuthenticated(self, id, password, **kw):
        """Get and authenticate an entry.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """
        return self._getEntryKW(id, password=password, **kw)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed(entry=entry)
        id = entry[self.id_field]
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
        self.checkDeleteEntryAllowed(id=id)
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        for info in self.getBackingDirectories():
            b_dir = info['dir']
            # Get id XXX maybe convert
            b_id = id
            b_dir.deleteEntry(b_id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        #print 'dir=%s rf=%s query=%s' % (self.id, return_fields, kw)

        schema = self._getSchemas()[0]
        all_field_ids = schema.keys()
        id_field = self.id_field

        # Compute query.
        query = {}
        for key, value in kw.items():
            if key not in all_field_ids:
                continue
            if not value:
                # Ignore empty searches.
                continue
            query[key] = value

        # Build queries for each backing dir
        b_queries = []
        for info in self.getBackingDirectories():
            b_dir = info['dir']
            field_ignore = info['field_ignore']
            field_rename = info['field_rename']
            field_rename_back = info['field_rename_back']
            b_field_ids = b_dir._getFieldIds()

            # Get sub-query
            b_query = {}
            for key, value in query.items():
                b_key = field_rename_back.get(key, key)
                if b_key in b_field_ids:
                    b_query[b_key] = value

            # Get return fields
            if return_fields is None:
                b_return_fields = None
            else:
                b_return_fields = []
                for fid in return_fields:
                    if fid == id_field:
                        # Won't be useful, we want the minimum
                        continue
                    b_fid = field_rename_back.get(fid, fid)
                    if b_fid in field_ignore:
                        continue
                    if b_fid not in b_field_ids:
                        continue
                    b_return_fields.append(b_fid)

            b_queries.append((info, b_return_fields, b_query))

        # Optimizations: find in what order to do the searches
        qs = []
        for info, b_return_fields, b_query in b_queries:
            if not b_return_fields and not b_query:
                # This query gets us no info and returns everything
                #print ' ignoring query on %s' % info['dir_id']
                continue
            qs.append((info, b_return_fields, b_query))

        # Do searches
        acc_res = None
        for info, b_return_fields, b_query in qs:
            b_dir = info['dir']

            # Do query
            #print ' subquery dir=%s rf=%s query=%s' % ( # XXX
            #    info['dir_id'], b_return_fields, b_query)
            b_res = b_dir.searchEntries(return_fields=b_return_fields,
                                        **b_query)
            #print ' res=%s' % `b_res`

            # Back-convert fields in query
            if return_fields is None:
                res = b_res
            else:
                res = []
                for id, b_entry in b_res:
                    entry = {}
                    for b_fid, value in b_entry.items():
                        fid = field_rename.get(b_fid, b_fid)
                        entry[fid] = value
                    res.append((id, entry))

            # Accumulate res into acc_res
            #print ' accumulating %s into %s' % (res, acc_res)
            if acc_res is None:
                acc_res = res
            else:
                # Do intelligent intersection
                if len(acc_res) > len(res):
                    acc_res, res = res, acc_res
                    # acc_res is now always smaller
                resids_d = {}
                if return_fields is None:
                    # Intersect
                    for id in res:
                        resids_d[id] = None
                    acc_res = [id for id in acc_res if resids_d.has_key(id)]
                else:
                    # Intersect and merge values for matching
                    for id, d in res:
                        resids_d[id] = d
                    old_res = acc_res
                    acc_res = []
                    for id, old_d in old_res:
                        new_d = resids_d.get(id)
                        if new_d is None:
                            continue
                        old_d.update(new_d)
                        acc_res.append((id, old_d))
            #print ' now acc_res=%s' % `acc_res`

        if acc_res is None:
            # No directories entries contributed at all...
            # Get all entries, with no information
            ids = self.listEntryIds()
            if return_fields is None:
                acc_res = ids
            else:
                acc_res = [(id, {}) for id in ids]

        if return_fields is not None and id_field in return_fields:
            # Re-add id if requested in return_fields
            for id, entry in acc_res:
                entry[id_field] = id

        #print '-> %s' % `acc_res`
        #LOG('searchEntries', DEBUG, 'rf=%s idf=%s sidf=%s res=%s' % (return_fields, id_field, self.id_field, acc_res))
        return acc_res

    #
    # Internal
    #

    def _getEntryFromBacking(self, id, field_ids, password=None):
        """Compute an entry from the backing directories."""
        entry = {self.id_field: id}
        for info in self.getBackingDirectories():
            b_dir = info['dir']
            field_ignore = info['field_ignore']
            field_rename = info['field_rename']
            # Get id XXX maybe convert
            b_id = id
            # Get field ids we want
            b_fids = []
            for b_fid in b_dir._getFieldIds():
                if b_fid == b_dir.id_field:
                    # Ignore id
                    continue
                if b_fid in field_ignore:
                    # Ignore fields ignored by mapping
                    continue
                fid = field_rename.get(b_fid, b_fid)
                if fid not in field_ids:
                    # Ignore fields unwanted in arguments
                    continue
                b_fids.append(b_fid)
            # Get entry (no acls checked)
            if password is not None and b_dir.isAuthenticating():
                b_entry = b_dir.getEntryAuthenticated(b_id, password,
                                                      field_ids=b_fids)
            else:
                if not b_fids:
                    continue
                b_entry = b_dir._getEntry(b_id, fields_ids=b_fids)
            # Keep what we need in entry
            for b_fid in b_fids:
                # Do renaming
                fid = field_rename.get(b_fid, b_fid)
                entry[fid] = b_entry[b_fid]
        return entry

InitializeClass(MetaDirectory)


class MetaStorageAdapter(BaseStorageAdapter):
    """Meta Storage Adapter

    This adapter gets and sets data from other backing directories.
    """

    def __init__(self, schema, id, dir, password=None, **kw):
        """Create an Adapter for a schema.

        The id passed is the member id. It may be None for creation.
        """
        self._id = id
        self._dir = dir
        self._password = password
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
        field_ids = [field_id for field_id, field in self.getFieldItems()]
        entry = self._dir._getEntryFromBacking(id, field_ids,
                                               password=self._password)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)
        dir = self._dir
        id = self._id

        # Do we assume we want to write all fields ?

        for info in dir.getBackingDirectories():
            b_dir = info['dir']
            field_ignore = info['field_ignore']
            field_rename = info['field_rename']

            # Get id XXX maybe convert
            b_id = id

            # Build backing entry
            b_entry = {}
            for b_fid in b_dir._getFieldIds():
                if b_fid == b_dir.id_field:
                    # Ignore id, already done.
                    continue
                if b_fid in field_ignore:
                    # Ignore fields ignored by mapping
                    continue
                fid = field_rename.get(b_fid, b_fid)
                if not data.has_key(fid):
                    # Skip fields missing in data
                    continue
                b_entry[b_fid] = data[fid]
            # Build id last to be sure it's there
            b_entry[b_dir.id_field] = b_id

            # Write or create to backing dir
            if self._do_create:
                b_dir.createEntry(b_entry)
            else:
                b_dir.editEntry(b_entry)

InitializeClass(MetaStorageAdapter)
