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
from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import Item_w__name__
from Products.CMFCore.CMFCorePermissions import ManagePortal

from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.CMFCore.utils import getToolByName, SimpleItemWithProperties
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter
from Products.CPSDirectory.BaseDirectory import BaseDirectory

class ProxyDirectory(SimpleItemWithProperties):
    """Proxy Directory.

    A directory that looks up another directory and passes all calls there.
    """

    meta_type = 'CPS Proxy Directory'

    security = ClassSecurityInfo()

    # Attributes:
    def _get_schema(self):
        return getattr(self._getContent(), 'schema', '')
    schema = ComputedAttribute(_get_schema, 1)

    def _get_schema_search(self):
        return getattr(self._getContent(), 'schema_search', '')
    schema_search = ComputedAttribute(_get_schema_search, 1)

    def _get_layout(self):
        return getattr(self._getContent(), 'layout', '')
    layout = ComputedAttribute(_get_layout, 1)

    def _get_layout_search(self):
        return getattr(self._getContent(), 'layout_search', '')
    layout_search = ComputedAttribute(_get_layout_search, 1)

    def _get_acl_access_roles(self):
        return getattr(self._getContent(), 'acl_access_roles', '')
    acl_access_roles = ComputedAttribute(_get_acl_access_roles, 1)

    def _get_acl_entry_create_roles(self):
        return getattr(self._getContent(), 'acl_entry_create_roles', '')
    acl_entry_create_roles = ComputedAttribute(_get_acl_entry_create_roles, 1)

    def _get_acl_entry_create_roles(self):
        return getattr(self._getContent(), 'acl_entry_delete_roles', '')
    acl_entry_delete_roles = ComputedAttribute(_get_acl_entry_create_roles, 1)

    def _get_acl_entry_edit_roles(self):
        return getattr(self._getContent(), 'acl_entry_edit_roles', '')
    acl_entry_edit_roles = ComputedAttribute(_get_acl_entry_edit_roles, 1)

    def _get_id_field(self):
        return getattr(self._getContent(), 'id_field', '')
    id_field = ComputedAttribute(_get_id_field, 1)

    def _get_title_field(self):
        return getattr(self._getContent(), 'title_field', '')
    title_field = ComputedAttribute(_get_title_field, 1)

    def _get_search_substring_fields(self):
        return getattr(self._getContent(), 'search_substring_fields', '')
    search_substring_fields = ComputedAttribute(_get_search_substring_fields, 1)

    def __init__(self, id, **kw):
        self.id = id
  
    def _getContent(self):
        """Get the content object, maybe editable."""
        try:
            tool = getToolByName(self, 'portal_membership', None)
            return tool.getHomeFolder()._getOb(self.getId())
        except AttributeError:
            return None

    security.declarePublic('isVisible')
    def isVisible(self):
        """Is the directory visible by the current user?"""
        ob = self._getContent()
        if not ob:
            return 0
        return ob.isVisible()

    security.declarePublic('isCreateEntryAllowed')
    def isCreateEntryAllowed(self):
        """Check that user can create an entry.

        Returns a boolean.
        """
        ob = self._getContent()
        if not ob:
            return 0
        return ob.isCreateEntryAllowed()

    security.declarePublic('isDeleteEntryAllowed')
    def isDeleteEntryAllowed(self):
        """Check that user can delete an entry.

        Returns a boolean.
        """
        ob = self._getContent()
        if not ob:
            return 0
        return ob.isDeleteEntryAllowed()

    security.declarePublic('isEditEntryAllowed')
    def isEditEntryAllowed(self, id=None, entry=None):
        # XXX should also have a new_entry arg.
        """Check that user can edit a given entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """
        ob = self._getContent()
        if not ob:
            return 0
        return ob.isEditEntryAllowed(id, entry)

    security.declarePublic('checkCreateEntryAllowed')
    def checkCreateEntryAllowed(self):
        """Check that user can create an entry.

        Raises Unauthorized if not.
        """
        ob = self._getContent()
        if not ob:
            raise Unauthorized("No create access to directory")
        return ob.checkCreateEntryAllowed()

    security.declarePublic('checkDeleteEntryAllowed')
    def checkDeleteEntryAllowed(self):
        """Check that user can delete an entry.

        Raises Unauthorized if not.
        """
        ob = self._getContent()
        if not ob:
            raise Unauthorized("No delete access to directory")
        return ob.checkDeleteEntryAllowed()

    security.declarePublic('checkEditEntryAllowed')
    def checkEditEntryAllowed(self, id=None, entry=None):
        """Check that user can edit a given entry.

        Raises Unauthorized if not.
        """
        ob = self._getContent()
        if not ob:
            raise Unauthorized("No edit access to entry '%s'" % id)
        return ob.checkEditEntryAllowed(id, entry)

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        ob = self._getContent()
        if not ob:
            return []
        return ob.listEntryIds()

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        ob = self._getContent()
        if not ob:
            return []
        return ob.listEntryIdsAndTitles()

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        ob = self._getContent()
        if not ob:
            return 0
        return ob.hasEntry(id)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        ob = self._getContent()
        if ob:
            return ob.createEntry(entry)

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        ob = self._getContent()
        if ob:
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
        if not ob:
            return []
        return ob.isVisible()

    security.declarePublic('editEntry')
    def editEntry(self, entry):
        """Edit an entry in the directory.
        """
        ob = self._getContent()
        if ob:
            return ob.editEntry(entry)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory.
        """
        ob = self._getContent()
        if ob:
            return ob.deleteEntry(id)

    security.declarePublic('getNewEntry')
    def getNewEntry(self, id):
        """Return a new clean entry for entry_id.
        """
        ob = self._getContent()
        if not ob:
            return {}
        return ob.getNewEntry(id)

    #
    # Rendering API
    #

    security.declarePublic('renderEntryDetailed')
    def renderEntryDetailed(self, id, layout_mode='view', **kw):
        """Render the entry.

        Returns (rendered, datastructure):
        - rendered is the rendered HTML,
        - datastructure is the resulting datastructure.
        """
        ob = self._getContent()
        if not ob:
            return ''
        return ob.renderEntryDetailed(id, layout_mode, **kw)

    # XXX security ?
    security.declarePublic('renderEditEntryDetailed')
    def renderEditEntryDetailed(self, id, request=None,
                                layout_mode='edit', layout_mode_err='edit',
                                **kw):
        """Modify the entry from request, returns detailed information
        about the rendering.

        If request is None, the entry is not modified and is rendered
        in layout_mode.

        If request is not None, the parameters are validated and the
        entry modified, and rendered in layout_mode. If there is
        a validation error, the entry is rendered in layout_mode_err.

        Returns (rendered, ok, datastructure):
        - rendered is the rendered HTML,
        - ok is the result of the validation,
        - datastructure is the resulting datastructure.
        """
        ob = self._getContent()
        if not ob:
            return ''
        return ob.renderEditEntryDetailed(id, request,
                                layout_mode, layout_mode_err, **kw)


    security.declarePublic('renderCreateEntryDetailed')
    def renderCreateEntryDetailed(self, request=None, validate=1,
                                  layout_mode='create',
                                  created_callback=None, **kw):
        """Render an entry for creation, maybe create it.

        Returns (rendered, ok, datastructure):
        - rendered is the rendered HTML,
        - ok is the result of the validation,
        - datastructure is the resulting datastructure.
        """
        ob = self._getContent()
        if not ob:
            return ''
        return ob.renderCreateEntryDetailed(request, validate,
                                  layout_mode, created_callback, **kw)

    security.declarePublic('renderSearchDetailed')
    def renderSearchDetailed(self, request=None, validate=0,
                             layout_mode='search', callback=None,
                             **kw):
        """Rendering for search.

        Calls callback when data has been validated.
        """
        ob = self._getContent()
        if not ob:
            return ''
        return ob.renderSearchDetailed(request, validate,
                             layout_mode, callback, **kw)
        
        
InitializeClass(ProxyDirectory)


