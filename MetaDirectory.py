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
from DateTime.DateTime import DateTime
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import getEngine

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.utils import QueryMatcher

from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed
from Products.CPSDirectory.BaseDirectory import ConfigurationError

from Products.CPSDirectory.interfaces import IMetaDirectory

from zope.interface import implements


class MetaDirectory(BaseDirectory):
    """Meta Directory

    A directory redirects requests to other backing directories.
    """
    implements(IMetaDirectory)

    meta_type = 'CPS Meta Directory'

    _properties = tuple(prop for prop in BaseDirectory._properties
                        if prop['id'] != 'search_substring_fields')

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
                             missing_entry_expr, delete=0, REQUEST=None):
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
            field_rename = {}
            for d in field_renames:
                field_rename[d['b_id']] = d['id']
            info['field_ignore'] = field_ignore
            info['field_rename'] = field_rename
            info['missing_entry_expr'] = missing_entry_expr
            new_infos.append(info)
        self.setBackingDirectories(new_infos)
        if REQUEST is not None:
            args = 'manage_tabs_message='+msg
            REQUEST.RESPONSE.redirect(self.absolute_url()+
                                      '/manage_editBackings?'+args)

    security.declareProtected(ManagePortal, 'manage_addBacking')
    def manage_addBacking(self, dir_id, field_ignore, field_renames,
                          missing_entry_expr, REQUEST=None):
        """Change mappings from ZMI."""
        infos = self.getBackingDirectories(no_dir=1)
        info = {'dir_id': dir_id.strip()}
        field_rename = {}
        for d in field_renames:
            field_rename[d['b_id']] = d['id']
        info['field_ignore'] = field_ignore
        info['field_rename'] = field_rename
        info['missing_entry_expr'] = missing_entry_expr
        infos.append(info)
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
                    raise ConfigurationError("No backing directory '%s'"
                                             % dir_id)
                info['dir'] = dir
            # Treat Upgrades
            if not info.has_key('missing_entry_expr'):
                info['missing_entry_expr'] = ''
                info['missing_entry'] = None
            infos.append(info)
        return infos

    security.declareProtected(ManagePortal, 'setBackingDirectories')
    def setBackingDirectories(self, infos):
        """Set the list of backing directories and their infos.

        Infos is a sequence of dicts with keys dir_id, id_conv,
        field_rename, field_ignore, missing_entry_expr.
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
            missing_entry_expr = (info.get('missing_entry_expr') or '').strip()
            if missing_entry_expr:
                expr = Expression(missing_entry_expr)
                expr_context = self._createMissingExpressionContext()
                missing_entry = expr(expr_context)
            else:
                missing_entry = None
            backing_dir_infos.append(
                {'dir_id': info['dir_id'],
                 'id_conv': info.get('id_conv'),
                 'field_rename': field_rename.copy(),
                 'field_rename_back': field_rename_back,
                 'field_ignore': field_ignore and tuple(field_ignore) or (),
                 'missing_entry_expr': missing_entry_expr,
                 'missing_entry': missing_entry,
                 })
        self.backing_dir_infos = tuple(backing_dir_infos)

    #
    # Internal API
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        dir = self
        adapters = [MetaStorageAdapter(schema, id, dir, **kw)
                    for schema in self._getSchemas(search=search)]
        return adapters


    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        # We get the ids from a directory with no missing entries.
        for info in self.getBackingDirectories():
            if info['missing_entry'] is None:
                return info['dir'].listEntryIds()
        return []

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        title_field = self.title_field
        if title_field == self.id_field:
            return [(id, id) for id in self.listEntryIds()]
        results = self._searchEntries(return_fields=[title_field])
        return [(id, entry[title_field]) for id, entry in results]

    security.declarePrivate('_hasEntry')
    def _hasEntry(self, id):
        """Does the directory have a given entry?"""
        # XXX should use base class implementation
        for info in self.getBackingDirectories():
            if info['missing_entry'] is None:
                return info['dir']._hasEntry(id)
        return 0

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.

        Asks the backing directories, one of them must be authenticating.
        """
        for info in self.getBackingDirectories():
            b_dir = info['dir']
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

    security.declarePrivate('_createEntry')
    def _createEntry(self, entry):
        """Create an entry in the directory."""
        id = entry[self.id_field]
        if self._hasEntry(id):
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

    security.declarePrivate('_deleteEntry')
    def _deleteEntry(self, id):
        """Delete an entry in the directory."""
        if not self._hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        for info in self.getBackingDirectories():
            b_dir = info['dir']
            # Get id XXX maybe convert
            b_id = id
            try:
                b_dir._deleteEntry(b_id)
            except KeyError:
                if info['missing_entry'] is None:
                    raise
                pass

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        # This search method has to take into account backing directories
        # that have a missing_entry property. There are several problems:
        # 1. generating missing entries in the result set when intersecting
        # 2. search on an attribute that's in a missing entry: FIXME not done.

        #print 'dir=%s rf=%s query=%s' % (self.id, return_fields, kw)

        all_field_ids = self._getFieldIds()
        id_field = self.id_field

        # Compute query.
        query = {}
        for key, value in kw.items():
            if key not in all_field_ids:
                continue
            if not value and value != False:
                # Ignore empty searches.
                continue
            query[key] = value

        # Build queries for each backing dir
        b_queries = []
        for info in self.getBackingDirectories():
            b_dir = info['dir']
            field_ignore = info['field_ignore']
            field_rename_back = info['field_rename_back']
            b_field_ids = b_dir._getFieldIds()
            b_id_field = b_dir.id_field

            # Get sub-query
            b_query = {}
            for key, value in query.items():
                b_key = field_rename_back.get(key, key)
                if b_key in b_field_ids:
                    b_query[b_key] = value
                    
            # checks if there's a missing entry and it matches the query
            missing_entry = info.get('missing_entry')
            if missing_entry is not None:
                matcher = QueryMatcher(b_query, accepted_keys=b_field_ids,
                                   substring_keys=b_dir.search_substring_fields)
                b_matched = matcher.match(missing_entry)
            else:
                b_matched = False

            # Get return fields
            if return_fields is None:
                b_return_fields = None
            elif return_fields == ['*']:
                b_return_fields = []
                for b_fid in b_field_ids:
                    if b_fid == b_id_field:
                        # Won't be useful, we want the minimum
                        continue
                    if b_fid in field_ignore:
                        continue
                    b_return_fields.append(b_fid)
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

            b_queries.append((info, b_return_fields, b_query, b_matched))

        # Find in what order to do the searches.
        # criterium: (normal < empty queries < matching missing_entry)

        # Search backing dirs with a matching missing_entry arelast
        # so that we can intersect with a fixed base.

        # Search backing dirs with empty queries are after normal ones, so
        # that the filtering algorithm will see that they aren't needed
        # to get a base list of entries to start the intersection process
        qs = []
        for qt in b_queries:
            info, b_return_fields, b_query, b_matched = qt
            if b_matched:
                order = 2
            elif not b_query:
                order = 1
            else:
                order = 0
            t = (order, qt)
            qs.append(t)
        qs.sort()
        b_queries = [t[1] for t in qs]

        # Remove useless queries:
        qs = []
        base_list_provides = False
        for qt in b_queries:
            info, b_return_fields, b_query, b_matched = qt
            if not b_return_fields and not b_query and base_list_provides:
                # This query gets us no info and returns everything
                # We must not skip it though if it's the first one to provide
                # a base list of entries, see comment above about the ordering
                #print ' ignoring query on %s' % info['dir_id']
                continue
            base_list_provides = base_list_provides or (not b_matched)
            qs.append(qt)
        b_queries = qs

        # Do searches
        acc_res = None
        for info, b_return_fields, b_query, b_matched in b_queries:
            b_dir = info['dir']
            missing_entry = info['missing_entry']
            b_field_rename = info['field_rename']
            has_missing_entries = missing_entry is not None

            # Do query
            #print ' subquery dir=%s rf=%s query=%s' % ( # XXX
            #    info['dir_id'], b_return_fields, b_query)
            b_res = b_dir._searchEntries(return_fields=b_return_fields,
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
                        fid = b_field_rename.get(b_fid, b_fid)
                        entry[fid] = value
                    res.append((id, entry))

            # Accumulate res into acc_res
            #print ' accumulating %s into %s' % (res, acc_res)
            if acc_res is None:
                acc_res = res
            else:
                if not b_matched:
                    # We don't care about ordering, let's prepare for
                    # quickest intersection by making acc_res the smaller one
                    if len(acc_res) > len(res):
                        acc_res, res = res, acc_res
                
                resids_d = {}
                if return_fields is None:
                    res_set = set(res)
                    if b_matched:
                        # previous results that matched the query or aren't in
                        # current backing 
                        acc_res = [id for id in acc_res
                                   if id in res_set or not b_dir._hasEntry(id)]
                    else:
                        acc_res = [id for id in acc_res if id in res_set]
                else:
                    # Intersect and merge values for matching
                    res_d = dict(res)
                    if b_matched:
                        # previous results that matched the query or aren't in
                        # current backing
                        acc_res = [(id,d) \
                                    for (id,d) in acc_res
                                    if id in res_d or not b_dir._hasEntry(id)]
                        for (id,d) in acc_res:
                            d.update(res_d.get(id, missing_entry))
                    else:
                        acc_res = [(id,d)
                                   for (id,d) in acc_res
                                   if id in res_d]
                        for (id,d) in acc_res:
                            d.update(res_d[id])

        if acc_res is None:
            # No directories entries contributed at all...
            # Get all entries, with no information
            ids = self.listEntryIds()
            if return_fields is None:
                acc_res = ids
            else:
                acc_res = [(id, {}) for id in ids]

        if (return_fields is not None and
            (return_fields == ['*'] or id_field in return_fields)):
            # Re-add id if requested in return_fields
            for id, entry in acc_res:
                entry[id_field] = id

        #print '-> %s' % `acc_res`
        #LOG('searchEntries', DEBUG, 'rf=%s idf=%s sidf=%s res=%s' % (return_fields, id_field, self.id_field, acc_res))
        return acc_res


    #
    # Hierarchical support
    #
    security.declarePrivate('_isHierarchical')
    def _isHierarchical(self):
        """Return true if one of the backing directory is hierarchical."""
        for info in self.getBackingDirectories():
            if info['missing_entry'] is None:
                if info['dir']._isHierarchical():
                    return True
        return False

    security.declarePrivate('_listChildrenEntryIds')
    def _listChildrenEntryIds(self, id, field_id=None):
        """Return a children entries ids for entry 'id'.

        Return a list of field_id if not None or self.id_field.
        Use the first hierarchical backing directory."""
        field_id = field_id or self.id_field
        for info in self.getBackingDirectories():
            if info['missing_entry'] is None:
                if info['dir']._isHierarchical():
                    return info['dir']._listChildrenEntryIds(id, field_id)
        raise ValueError(
            "No Hierarchical backing directory for [%s] found." % self.getId())


    security.declarePrivate('_getParentEntryId')
    def _getParentEntryId(self, id):
        """Return Parent Id of 'id'.

        Return None if 'id' have no parent.
        Return a field_id if not None or a self.id_field.
        Use the first hierarchical backing directory."""
        field_id = field_id or self.id_field
        for info in self.getBackingDirectories():
            if info['missing_entry'] is None:
                if info['dir']._isHierarchical():
                    return info['dir']._getParentEntryId(id, field_id)
        raise ValueError(
            "No Hierarchical backing directory for [%s] found." % self.getId())

    #
    # Internal
    #

    def _createMissingExpressionContext(self):
        """Create an expression context for missing entry computation."""
        mapping = {
            'portal': getToolByName(self, 'portal_url').getPortalObject(),
            'DateTime': DateTime,
            'nothing': None,
            }
        return getEngine().getContext(mapping)

    def _getEntryFromBacking(self, id, field_ids, password=None,
                             missing_fields=None):
        """Compute an entry from the backing directories.

        If missing_fields (a list) is provided, keep a trace of fields coming
        from missing entry in them.
        """
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
                try:
                    b_entry = b_dir._getEntry(b_id, fields_ids=b_fids)
                except KeyError:
                    missing_entry = info['missing_entry']
                    if missing_entry is None:
                        raise
                    b_entry = missing_entry
                    missing_fields.extend(missing_entry.keys())
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
        self._missing_fields = []
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
                                               password=self._password,
                                               missing_fields=self._missing_fields,)
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
                b_dir._createEntry(b_entry)
            else:
                try:
                    b_dir._editEntry(b_entry)
                except KeyError:
                    if info['missing_entry'] is None:
                        raise
                    # missing entry must take precedence over field defaults
                    # typically for consistency with what was read
                    # before performing the write.
                    merged = info['missing_entry']
                    merged.update(b_entry)
                    b_dir._createEntry(merged)

    def _getContentUrl(self, entry_id, field_id):
        """ giving content url if backing has it"""
        result = None
        entry, b_dir = self._dir._getEntryFromBacking(self._id)

        if b_dir is not None:
            # we need to check for ids
            if b_dir.id_field <> self._dir.id_field:
                entry_id = entry[b_dir.id_field]
            child_adapter = b_dir._getAdapters(id)[0]
            if getattr(child_adapter, '_getContentUrl', None) is not None:
                result = child_adapter._getContentUrl(entry_id, field_id)
        return result

InitializeClass(MetaStorageAdapter)
