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

from zLOG import LOG, DEBUG

from cgi import escape
from types import ListType, TupleType, StringType
from Globals import Persistent
from Globals import InitializeClass
from Acquisition import Implicit
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl.Role import RoleManager
from OFS.SimpleItem import Item_w__name__
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CPSSchemas.PropertiesPostProcessor import PropertiesPostProcessor
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter
from Products.CPSDirectory.BaseDirectory import BaseDirectory


class ZODBDirectory(PropertiesPostProcessor, BTreeFolder2, BaseDirectory):
    """ZODB Directory.

    A directory that stores its data in the ZODB.

    The entries are individual subobjects where the values are stored as
    simple attributes.
    """

    meta_type = 'CPS ZODB Directory'

    security = ClassSecurityInfo()

    id_field = 'id'
    title_field = 'id'

    def __init__(self, id, **kw):
        BTreeFolder2.__init__(self, id)
        BaseDirectory.__init__(self, id, **kw)

    _properties = BaseDirectory._properties
    _properties_post_process_split = BaseDirectory._properties_post_process_split
    _properties_post_process_tales = BaseDirectory._properties_post_process_tales

    #
    # ZMI
    #

    manage_options = (
        BaseDirectory.manage_options[:1] + # Properties
        BTreeFolder2.manage_options[0:1] + # Contents
        BaseDirectory.manage_options[1:]
        )

    #
    # API
    #

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
        schema = self._getSchemas()[0]
        adapter = AttributeStorageAdapter(schema, None,
                                          field_ids=[title_field])
        res = []
        for id, ob in self.objectItems():
            adapter.setContextObject(ob)
            entry = adapter.getData()
            res.append((id, entry[title_field]))
        return res

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        return self.hasObject(id)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed()
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise KeyError("Entry '%s' already exists" % id)
        ob = ZODBDirectoryEntry()
        ob._setId(id)
        self._setObject(id, ob)
        if hasattr(ob, '__ac_local_roles__'):
            # Cleanup object for minimal memory usage.
            delattr(ob, '__ac_local_roles__')
        self.editEntry(entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed()
        if not self.hasEntry(id):
            raise KeyError("Entry '%s' does not exist" % id)
        self._delObject(id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.
        """
        schema = self._getSchemas()[0]
        all_field_ids = schema.keys()

        # Compute search_types and query.
        search_types = {}
        query = {}
        for key, value in kw.items():
            if key not in all_field_ids:
                continue
            if not value:
                # Ignore empty searches.
                continue
            if isinstance(value, StringType):
                if key in self.search_substring_fields:
                    search_types[key] = 'substring'
                    value = value.lower()
                else:
                    search_types[key] = 'exact'
            elif isinstance(value, ListType) or isinstance(value, TupleType):
                search_types[key] = 'list'
            else:
                raise ValueError("Bad value %s for '%s'" % (`value`, key))
            query[key] = value

        # Compute needed fields from object.
        # All fields we need to return.
        field_ids_d = {self.id_field: None}
        if return_fields is not None:
            if return_fields == ['*']:
                return_fields = all_field_ids
            for field_id in return_fields:
                if field_id not in all_field_ids:
                    continue
                field_ids_d[field_id] = None
                dep_ids = schema[field_id].read_process_dependent_fields
                for dep_id in dep_ids:
                    field_ids_d[dep_id] = None
        # Also all fields the search is made on.
        for key in query.keys():
            field_ids_d[key] = None
        field_ids = field_ids_d.keys()

        # Do the search.
        schema = self._getSchemas()[0]
        adapter = AttributeStorageAdapter(schema, None,
                                          field_ids=field_ids)
        res = []
        for id, ob in self.objectItems():
            adapter.setContextObject(ob)
            entry = adapter.getData()
            ok = 1
            for key, value in query.items():
                searched = entry[key]
                if isinstance(searched, StringType):
                    searched = (searched,)
                matched = 0
                for item in searched:
                    if search_types[key] == 'list':
                        matched = item in value
                    elif search_types[key] == 'substring':
                        matched = item.lower().find(value) != -1
                    else: # search_types[key] == 'exact':
                        matched = item == value
                    if matched:
                        break
                if not matched:
                    ok = 0
                    break
            if not ok:
                continue
            # Compute result to return.
            if return_fields is None:
                res.append(id)
            else:
                d = {}
                for key in return_fields:
                    d[key] = entry[key]
                res.append((id, d))
        return res

    #
    # Internal
    #

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, **kw):
        """Get the adapters for an entry."""
        if id is not None:
            ob = self._getOb(id)
        else:
            # Creation
            ob = None
        adapters = [AttributeStorageAdapter(schema, ob, **kw)
                    for schema in self._getSchemas()]
        return adapters

InitializeClass(ZODBDirectory)


class ZODBDirectoryEntry(Item_w__name__,
                         Persistent, Implicit, RoleManager):
    """ZODB Directory Entry.

    Stores all data from an entry.
    """
    # Item_w__name__ is used so that the 'id' attribute is free.

    security = ClassSecurityInfo()

    __name__ = 'no__name__'

    def getId(self):
        """Return the id of the object."""
        return self.__name__

    manage_options = (
        ({'label': 'View', 'action': 'manage_main'},
         ) + Item_w__name__.manage_options +
        ({'label': 'Security', 'action': 'manage_access',
          'help': ('OFSP', 'Security.stx')},
         )
        )

    security.declareProtected(ManagePortal, 'manage_main')
    def manage_main(self, REQUEST=None, RESPONSE=None):
        """View object. XXX"""
        res = ['<html>']
        for id, value in self.__dict__.items():
            res.append('<b>%s</b>: %s<br />'
                       % (escape(str(id)), escape(str(value))))
        res.append('</html>')
        return '\n'.join(res)
