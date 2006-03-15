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
"""ZODBDirectory
"""

from zLOG import LOG, DEBUG, TRACE

from cgi import escape
from copy import deepcopy
from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from OFS.Cache import Cacheable

from Products.CMFCore.permissions import ManagePortal
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2

from Products.CPSUtil.PropertiesPostProcessor import PropertiesPostProcessor
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter

from Products.CPSDirectory.utils import QueryMatcher
from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed

from Products.CPSDirectory.interfaces import IContentishDirectory

from zope.interface import implements


class ZODBDirectory(PropertiesPostProcessor, BTreeFolder2,
                    BaseDirectory, Cacheable):
    """ZODB Directory.

    A directory that stores its data in the ZODB.

    The entries are individual subobjects where the values are stored as
    simple attributes.
    """
    implements(IContentishDirectory)

    meta_type = 'CPS ZODB Directory'

    security = ClassSecurityInfo()

    def __init__(self, id, **kw):
        BTreeFolder2.__init__(self, id)
        BaseDirectory.__init__(self, id, **kw)

    _properties = BaseDirectory._properties + (
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': "Field for password (if authentication)"},
        )
    password_field = ''

    id_field = 'id'
    title_field = 'id'

    _properties_post_process_split = BaseDirectory._properties_post_process_split
    _properties_post_process_tales = BaseDirectory._properties_post_process_tales

    #
    # ZMI
    #

    manage_options = (
        BaseDirectory.manage_options[:1] + # Properties
        BTreeFolder2.manage_options[0:1] + # Contents
        BaseDirectory.manage_options[1:]
        ) + Cacheable.manage_options

    #
    # API
    #

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        PropertiesPostProcessor._postProcessProperties(self)
        self.ZCacheable_invalidate()

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        return list(self.objectIds())

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        title_field = self.title_field
        if title_field == self.id_field:
            return [(id, id) for id in self.objectIds()]

        # Get all the fields that title may depend on
        field_ids_d = {title_field: None}
        schema = self._getUniqueSchema()
        dep_ids = schema[title_field].read_process_dependent_fields
        for dep_id in dep_ids:
            field_ids_d[dep_id] = None
        field_ids = field_ids_d.keys()
        adapter = AttributeStorageAdapter(schema, None, field_ids=field_ids)
        res = []
        for id, ob in self.objectItems():
            adapter.setContextObject(ob)
            entry = adapter.getData()
            adapter.finalizeDefaults(entry)
            res.append((id, entry[title_field]))
        return res

    security.declarePrivate('_hasEntry')
    def _hasEntry(self, id):
        """Does the directory have a given entry?"""
        return self.hasObject(id)

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.
        """
        return not not self.password_field

    security.declarePrivate('getEntryAuthenticated')
    def getEntryAuthenticated(self, id, password, **kw):
        """Get and authenticate an entry.

        Doesn't check ACLs.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """
        entry = self._getEntryKW(id, **kw) # may raise KeyError
        password_field = self.password_field
        cur_password = entry.get(password_field)
        if cur_password is None:
            LOG('getEntryAuthenticated', TRACE, "No field '%s' for %s in %s" %
                (password_field, id, self.getId()))
            raise AuthenticationFailed
        if not self._checkPassword(password, cur_password):
            LOG('getEntryAuthenticated', TRACE,
                "Authentication failed for %s in %s" % (id, self.getId()))
            raise AuthenticationFailed
        return entry

    security.declarePrivate('_createEntry')
    def _createEntry(self, entry):
        """@summary: Create an entry in the directory.

        Set the isUserModified flag

        @param entry: dictionnary of entry values
        @type: @Dict
        """
        id = entry.get(self.id_field)
        if id is None:
            raise KeyError("Entry data must have '%s' field" % self.id_field)
        if self._hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)
        ob = ZODBDirectoryEntry()
        ob._setId(id)
        self._setObject(id, ob)
        if hasattr(ob, '__ac_local_roles__'):
            # Cleanup object for minimal memory usage.
            try:
                delattr(ob, '__ac_local_roles__')
            except (AttributeError, KeyError):
                # ExtensionClasses raise KeyError... duh.
                pass
        self._editEntry(entry)
        if not self.isUserModified():
            self.setUserModified(True)

    security.declarePrivate('_editEntry')
    def _editEntry(self, entry, check_acls=False):
        """ unrestricted method to edit an entry and invalidate the cache. """
        BaseDirectory._editEntry(self, entry, check_acls)
        self.ZCacheable_invalidate()

    security.declarePrivate('_deleteEntry')
    def _deleteEntry(self, id):
        """@summary: Delete an entry in the directory.

        Set the isUserModified flag

        @param id: entry identifiant
        @type id: @String
        """
        if not self._hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        self._delObject(id)
        if not self.isUserModified():
            self.setUserModified(True)
        self.ZCacheable_invalidate()

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.
        """
        if self.ZCacheable_isCachingEnabled():
            keyset = {'return_fields' : return_fields}
            keyset.update(kw)
            LOG('ZODBDirectory._searchEntries', TRACE,
                "Searching cache for %s" % (keyset,))
            from_cache = self.ZCacheable_get(keywords=keyset)
            if from_cache is not None:
                LOG('ZODBDirectory._searchEntries', TRACE, " -> results=%s" %
                    (from_cache[:20],))
                return deepcopy(from_cache)
        else:
            keyset = None

        matcher = QueryMatcher(kw, accepted_keys=self._getFieldIds(),
                               substring_keys=self.search_substring_fields)

        # Compute needed fields from object.
        # All fields we need to return.
        field_ids_d, return_fields = self._getSearchFields(return_fields)
        # Add all fields the search is made on.
        field_ids = matcher.getKeysSet().union(field_ids_d)

        # Do the search.
        schema = self._getUniqueSchema()
        adapter = AttributeStorageAdapter(schema, None,
                                          field_ids=list(field_ids))
        res = []
        for id, ob in self.objectItems():
            adapter.setContextObject(ob)
            entry = adapter.getData()
            adapter.finalizeDefaults(entry)
            if not matcher.match(entry):
                continue
            # Compute result to return.
            if return_fields is None:
                res.append(id)
            else:
                d = {}
                for key in return_fields:
                    d[key] = entry[key]
                res.append((id, d))

        if keyset is not None:
            LOG('ZODBDirectory._searchEntries', TRACE, "Putting in cache")
            self.ZCacheable_set(res, keywords=keyset)

        return deepcopy(res)

    #
    # Internal
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        if id is not None:
            ob = self._getOb(id)
        else:
            # Creation
            ob = None
        adapters = [AttributeStorageAdapter(schema, ob, **kw)
                    for schema in self._getSchemas(search=search)]
        return adapters

    security.declarePrivate('_checkPassword')
    def _checkPassword(self, candidate, password):
        """Check that a password is correct.

        Returns a boolean.
        """
        return (candidate == password)

InitializeClass(ZODBDirectory)


class ZODBDirectoryEntry(SimpleItem):
    """ZODB Directory Entry.

    Stores all data from an entry.
    """
    # SimpleItem is used so that the 'id' attribute is free.

    security = ClassSecurityInfo()

    __name__ = 'no__name__'

    def getId(self):
        """Return the id of the object."""
        return self.__name__

    manage_options = (
        ({'label': 'View', 'action': 'manage_main'},
         ) + SimpleItem.manage_options +
        ({'label': 'Security', 'action': 'manage_access',
          'help': ('OFSP', 'Security.stx')},
         )
        )

    security.declareProtected(ManagePortal, 'manage_main')
    def manage_main(self, REQUEST=None, RESPONSE=None):
        """View object. XXX"""
        res = ['<html>']
        for id, value in self.__dict__.items():
            res.append('<strong>%s</strong>: %s<br />'
                       % (escape(str(id)), escape(str(value))))
        res.append('</html>')
        return '\n'.join(res)
