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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from ComputedAttribute import ComputedAttribute

from Products.CMFCore.utils import getToolByName
from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.ZODBDirectory import ZODBDirectory

class LocalDirectory(BaseDirectory):
    """A Directory that acts as a Proxy to a directory in the UserHomeFolder.
    """

    meta_type = 'CPS Local Directory'  

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'directory_id', 'type': 'string', 'mode': 'w',
         'label': 'Id of local directory'},
        )

    # Attributes:
    def _get_schema(self):
        return getattr(self.getProperty('schema', ''))
    schema = ComputedAttribute(_get_schema, 1)

    def _get_schema_search(self):
        return getattr(self.getProperty('schema_search', ''))
    schema_search = ComputedAttribute(_get_schema_search, 1)

    def _get_layout(self):
        return getattr(self.getProperty('layout', ''))
    layout = ComputedAttribute(_get_layout, 1)

    def _get_layout_search(self):
        return getattr(self.getProperty('layout_search', ''))
    layout_search = ComputedAttribute(_get_layout_search, 1)

    def _get_acl_directory_view_roles(self):
        return getattr(self.getProperty('acl_directory_view_roles', ''))
    acl_directory_view_roles = ComputedAttribute(_get_acl_directory_view_roles, 1)

    def _get_acl_entry_create_roles(self):
        return getattr(self.getProperty('acl_entry_create_roles', ''))
    acl_entry_create_roles = ComputedAttribute(_get_acl_entry_create_roles, 1)

    def _get_acl_entry_create_roles(self):
        return getattr(self.getProperty('acl_entry_delete_roles', ''))
    acl_entry_delete_roles = ComputedAttribute(_get_acl_entry_create_roles, 1)

    def _get_acl_entry_view_roles(self):
        return getattr(self.getProperty('acl_entry_view_roles', ''))
    acl_entry_view_roles = ComputedAttribute(_get_acl_entry_view_roles, 1)

    def _get_acl_entry_edit_roles(self):
        return getattr(self.getProperty('acl_entry_edit_roles', ''))
    acl_entry_edit_roles = ComputedAttribute(_get_acl_entry_edit_roles, 1)

    def _get_id_field(self):
        return getattr(self.getProperty('id_field', ''))
    id_field = ComputedAttribute(_get_id_field, 1)

    def _get_title_field(self):
        return getattr(self.getProperty('title_field', ''))
    title_field = ComputedAttribute(_get_title_field, 1)

    def _get_search_substring_fields(self):
        return getattr(self.getProperty('search_substring_fields', ''))
    search_substring_fields = ComputedAttribute(_get_search_substring_fields, 1)

    def __init__(self, id, **kw):
        self.id = id
        self.directory_id = ''
  
    def getProperty(self, id, d=None):
        """Get the content object, maybe editable."""
        tool = getToolByName(self, 'portal_membership', None)
        folder = tool.getHomeFolder()
        try:
            ob = folder._getOb(self.directory_id)
            return getattr(ob, id, d)
        except AttributeError:
            if id in self.__dict__.keys():
                return self.__dict__[id]
            else:
                return d

    def _getContent(self):
        """Get the content object, maybe editable."""
        tool = getToolByName(self, 'portal_membership', None)
        folder = tool.getHomeFolder()
        if folder is None:
            raise KeyError("Home folder could not be found. " \
                "Maybe you are not a member of this portal?")
        try:
            return folder._getOb(self.directory_id)
        except AttributeError:
            pass 
        # The local directory could not be found. Try creating it.
        # (Creates a ZODB Directory, because nothing else really
        # makes sense at the moment. In the future maybe it should be
        # a setting?)
        props = {}
        for prop in self.propertyIds():
            props[prop] = self.getProperty(prop)
        new_dir = ZODBDirectory(self.directory_id, **props)
        folder._setObject(self.directory_id, new_dir)
        return folder._getOb(self.directory_id)

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        ob = self._getContent()
        return ob.listEntryIds()

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
        ob = self._getContent()
        return ob.hasEntry(id)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        ob = self._getContent()
        return ob.createEntry(entry)

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        ob = self._getContent()
        return ob.getEntry(id)

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        The keyword arguments specify the search to be done.
        It is of the form {field1: value1, field2: [value21, value22]...}

        The search is done:

          - As a substring case-independent search for fields in
            search_substring_fields.

          - As an exact search for all other fields.

          - Searches done for a list values are always OR exact searches.

        If return_fields is None, returns a list of ids:
          ['member1', 'member2']

        If return_fields is not None, it must be sequence of field ids.
        The method will return a list of tuples containing the member id
        and a dictionary of available fields:
          [('member1', {'email': 'foo', 'age': 75}), ('member2', {'age': 5})]

        return_fields=['*'] means to return all available fields.
        """
        ob = self._getContent()
        return ob.searchEntries(return_fields, **kw)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory.
        """
        ob = self._getContent()
        return ob.deleteEntry(id)

    # These next two are probably not needed, since they are internal.
    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, **kw):
        """Get the adapters for an entry."""
        ob = self._getContent()
        return ob._getAdapters(id, **kw)

    security.declarePrivate('_getAdditionalRoles')
    def _getAdditionalRoles(self, id):
        ob = self._getContent()
        return ob._getAdditionalRoles(id)
    
InitializeClass(LocalDirectory)


