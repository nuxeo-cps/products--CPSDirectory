# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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
"""BaseDirectory
"""

from zLOG import LOG, DEBUG

from urllib import urlencode

from Globals import InitializeClass
from Globals import DTMLFile
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Unauthorized
from AccessControl import ModuleSecurityInfo
from DateTime.DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CMFCore.CMFCorePermissions import ManagePortal
from Products.CMFCore.Expression import Expression
from Products.CMFCore.Expression import getEngine
from Products.PageTemplates.TALES import CompilerError

from Products.CPSSchemas.PropertiesPostProcessor import PropertiesPostProcessor
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.Field import ReadAccessError
from Products.CPSSchemas.Field import WriteAccessError


_marker = []


class AuthenticationFailed(Exception):
    """Raised when authentication fails."""
    pass


class SearchSizeLimitExceeded(Exception):
    """Raised when a search returns too many results."""
    pass
ModuleSecurityInfo('Products.CPSDirectory.BaseDirectory').declarePublic('SearchSizeLimitExceeded')


class ConfigurationError(ValueError):
    """Raised when a directory is misconfigured."""
    pass


# Utility functions for _properties, should be elsewhere
def _replaceProperty(props, id, prop):
    res = []
    for d in props:
        if d['id'] == id:
            if prop is not None:
                res.append(prop)
            continue
        res.append(d)
    return tuple(res)


class BaseDirectory(PropertiesPostProcessor, SimpleItemWithProperties):
    """Base Directory.

    A directory holds information about entries and how to access and
    display them.
    """

    meta_type = None

    security = ClassSecurityInfo()

    _propertiesBaseClass = SimpleItemWithProperties
    _properties = SimpleItemWithProperties._properties + (
        {'id': 'schema', 'type': 'string', 'mode': 'w',
         'label': "Schema"},
        {'id': 'schema_search', 'type': 'string', 'mode': 'w',
         'label': "Schema for search"},
        {'id': 'layout', 'type': 'string', 'mode': 'w',
         'label': "Layout"},
        {'id': 'layout_search', 'type': 'string', 'mode': 'w',
         'label': "Layout for search"},
        {'id': 'acl_directory_view_roles', 'type': 'string', 'mode': 'w',
         'label': "ACL: directory view roles"},
        {'id': 'acl_entry_create_roles', 'type': 'string', 'mode': 'w',
         'label': "ACL: entry create roles"},
        {'id': 'acl_entry_delete_roles', 'type': 'string', 'mode': 'w',
         'label': "ACL: entry delete roles"},
        {'id': 'acl_entry_view_roles', 'type': 'string', 'mode': 'w',
         'label': "ACL: entry view roles"},
        {'id': 'acl_entry_edit_roles', 'type': 'string', 'mode': 'w',
         'label': "ACL: entry edit roles"},
        {'id': 'id_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry id'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        {'id': 'search_substring_fields', 'type': 'tokens', 'mode': 'w',
         'label': 'Fields with substring search'},
        )

    schema = ''
    schema_search = ''
    layout = ''
    layout_search = ''
    acl_directory_view_roles = 'Manager; Member'
    acl_entry_create_roles = 'Manager'
    acl_entry_delete_roles = 'Manager'
    acl_entry_view_roles = 'Manager; Member'
    acl_entry_edit_roles = 'Manager'
    id_field = ''
    title_field = ''
    search_substring_fields = []

    entry_roles = []

    acl_directory_view_roles_c = ['Manager', 'Member']
    acl_entry_create_roles_c = ['Manager']
    acl_entry_delete_roles_c = ['Manager']
    acl_entry_view_roles_c = ['Manager', 'Member']
    acl_entry_edit_roles_c = ['Manager']

    _properties_post_process_split = (
        ('acl_directory_view_roles', 'acl_directory_view_roles_c', ',; '),
        ('acl_entry_create_roles', 'acl_entry_create_roles_c', ',; '),
        ('acl_entry_delete_roles', 'acl_entry_delete_roles_c', ',; '),
        ('acl_entry_view_roles', 'acl_entry_view_roles_c', ',; '),
        ('acl_entry_edit_roles', 'acl_entry_edit_roles_c', ',; '),
        )
    _properties_post_process_tales = ()

    def __init__(self, id, **kw):
        self.id = id
        self.manage_changeProperties(**kw)
        self.user_modified = 0

    #
    # Usage API
    #

    security.declarePublic('isUserModified')
    def isUserModified(self):
        """
        @summary: Return if the object has been modified by users.
        @rtype: @Boolean
        """
        if not hasattr(self, 'user_modified'):
            return 0
        return self.user_modified

    security.declarePublic('setUserModified')
    def setUserModified(self, user_modified):
        """
        @summary: Set if the object has been modified by users.
        @param user_modified: boolean value
        @type user_modified: @Boolean
        """
        self.user_modified = user_modified

    security.declarePrivate('isEntryAclAllowed')
    def isEntryAclAllowed(self, acl_roles, id=None, entry=None):
        """@summary: Check if the user has correct ACL on an entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        @rtype: @Boolean
        """
        if entry is None:
            if id is not None:
                entry = self._getEntry(id)
            else:
                entry = {}
        if id is None:
            id = entry.get(self.id_field)
        roles = getSecurityManager().getUser().getRolesInContext(self)
        add_roles = self._getAdditionalRoles(id)
        entry_local_roles = self.getEntryLocalRoles(entry)
        all_roles = list(roles) + list(add_roles) + list(entry_local_roles)
        for r in acl_roles:
            if r in all_roles:
                return 1
        return 0

    security.declarePublic('isVisible')
    def isVisible(self):
        """Check if the user can view the directory.

        Uses the computed entry local roles.

        Returns a boolean.
        """
        return self.isEntryAclAllowed(self.acl_directory_view_roles_c)

    security.declarePublic('isCreateEntryAllowed')
    def isCreateEntryAllowed(self, id=None, entry=None):
        """Check if the user can create an entry.

        Uses the computed entry local roles.

        Returns a boolean.
        """
        if entry is None:
            if id is not None:
                entry = {self.id_field: id}
            else:
                entry = {}
        return self.isEntryAclAllowed(self.acl_entry_create_roles_c,
                                      id=id, entry=entry)

    security.declarePublic('isDeleteEntryAllowed')
    def isDeleteEntryAllowed(self, id=None, entry=None):
        """Check if the user can delete an entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """
        return self.isEntryAclAllowed(self.acl_entry_delete_roles_c,
                                      id=id, entry=entry)

    security.declarePublic('isViewEntryAllowed')
    def isViewEntryAllowed(self, id=None, entry=None):
        """Check if the user can view an entry.

        Returns a boolean.
        """
        return self.isEntryAclAllowed(self.acl_entry_view_roles_c,
                                      id=id, entry=entry)

    security.declarePublic('isEditEntryAllowed')
    def isEditEntryAllowed(self, id=None, entry=None):
        # XXX should also have a new_entry arg.
        """Check if the user can edit a given entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """
        return self.isEntryAclAllowed(self.acl_entry_edit_roles_c,
                                      id=id, entry=entry)

    security.declarePublic('isSearchEntriesAllowed')
    def isSearchEntriesAllowed(self):
        # XXX should also have a new_entry arg.
        """Check if the user can search entries within the directory.

        Equivalent to isVisible, because it uses directory view roles.
        Uses the computed entry local roles.

        Returns a boolean.
        """
        return self.isEntryAclAllowed(self.acl_directory_view_roles_c)

    security.declarePublic('checkCreateEntryAllowed')
    def checkCreateEntryAllowed(self, id=None, entry=None):
        """Check that the user can create an entry.

        Raises Unauthorized if not.
        """
        if not self.isCreateEntryAllowed(id=id, entry=entry):
            raise Unauthorized("No create access to directory")

    security.declarePublic('checkDeleteEntryAllowed')
    def checkDeleteEntryAllowed(self, id=None, entry=None):
        """Check that the user can delete a given entry.

        Raises Unauthorized if not.
        """
        if not self.isDeleteEntryAllowed(id=id, entry=entry):
            raise Unauthorized("No delete access to entry")

    security.declarePublic('checkViewEntryAllowed')
    def checkViewEntryAllowed(self, id=None, entry=None):
        """Check that the user can view a given entry.

        Raises Unauthorized if not.
        """
        if not self.isViewEntryAllowed(id=id, entry=entry):
            raise Unauthorized("No view access to entry")

    security.declarePublic('checkEditEntryAllowed')
    def checkEditEntryAllowed(self, id=None, entry=None):
        """Check that the user can edit a given entry.

        Raises Unauthorized if not.
        """
        if not self.isEditEntryAllowed(id=id, entry=entry):
            raise Unauthorized("No edit access to entry '%s'" % id)

    security.declarePublic('checkSearchEntriesAllowed')
    def checkSearchEntriesAllowed(self):
        """Check that the user can search entries.

        Actually checks if the user can view entries.
        Raises Unauthorized if not.
        """
        if not self.isSearchEntriesAllowed():
            raise Unauthorized("No search access to directory")

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        raise NotImplementedError

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """
        # Default dummy implementation.
        return [(id, id) for id in self.listEntryIds()]

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        raise NotImplementedError

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.

        Returns the id given to the entry if different from the one given
        or None.
        """
        raise NotImplementedError

    security.declarePublic('getEntry')
    def getEntry(self, id, default=_marker):
        """Get entry filtered by acls and processes.

        A default argument can be specified so that KeyError is not
        raised if the entry does not exist.
        """
        try:
            return self._getEntryKW(id)
        except (KeyError, ValueError):
            if default is not _marker:
                return default
            else:
                raise

    security.declarePrivate('_getEntryFromDataModel')
    def _getEntryFromDataModel(self, datamodel):
        """Compute dict from datamodel."""
        entry = {}
        for key in datamodel.keys():
            try:
                entry[key] = datamodel[key]
            except ReadAccessError:
                pass
        return entry

    security.declarePrivate('_getEntryKW')
    def _getEntryKW(self, id, **kw):
        """Get entry filtered by acls and processes.

        Passes additional **kw to _getDataModel.
        """
        dm = self._getDataModel(id, **kw)
        return self._getEntryFromDataModel(dm)

    security.declarePrivate('_getEntry')
    def _getEntry(self, id, **kw):
        """Get entry filtered by processes but not acls."""
        dm = self._getDataModel(id, check_acls=0, **kw)
        return self._getEntryFromDataModel(dm)

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.
        """
        return 0

    security.declarePrivate('getEntryAuthenticated')
    def getEntryAuthenticated(self, id, password, **kw):
        """Get and authenticate an entry.

        Doesn't check ACLs.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """
        raise AuthenticationFailed

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
        self.checkSearchEntriesAllowed()
        return self._searchEntries(return_fields=return_fields, **kw)

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory, unrestricted.

        See documentation on searchEntries().
        This private method does not do ACL checks.
        """
        raise NotImplementedError

    security.declarePublic('editEntry')
    def editEntry(self, entry):
        """Edit an entry in the directory.
        """
        id = entry[self.id_field]
        dm = self._getDataModel(id)
        dm_entry = self._getEntryFromDataModel(dm)
        self.checkEditEntryAllowed(id=id, entry=dm_entry)
        for key in dm.keys():
            if not entry.has_key(key):
                continue
            try:
                dm[key] = entry[key]
            except WriteAccessError:
                pass
        dm._commit()

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory.
        """
        raise NotImplementedError

    security.declarePublic('getNewEntry')
    def getNewEntry(self, id):
        """Return a new clean entry for entry_id.
        """
        raise NotImplementedError

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
        dm = self._getDataModel(id)
        entry = self._getEntryFromDataModel(dm)
        self.checkViewEntryAllowed(id=id, entry=entry)
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout()
        layout.prepareLayoutWidgets(ds)
        layout_structure = layout.computeLayoutStructure(layout_mode, dm)
        rendered = self._renderLayout(layout_structure, ds,
                                      layout_mode=layout_mode, **kw)
        return rendered, ds

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
        dm = self._getDataModel(id)
        entry = self._getEntryFromDataModel(dm)
        self.checkEditEntryAllowed(id=id, entry=entry)
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout()
        layout.prepareLayoutWidgets(ds)
        if request is None:
            validate = 0
        else:
            validate = 1
            ds.updateFromMapping(request.form)
        layout_structure = layout.computeLayoutStructure(layout_mode, dm)
        if validate:
            ok = layout.validateLayoutStructure(layout_structure, ds,
                                                layout_mode=layout_mode, **kw)
            id_field = self.id_field
            if not ds.hasError(id_field) and dm.data[id_field] != id:
                ds.setError(id_field, 'cpsschemas_err_readonly')
                ok = 0
            if ok:
                dm._commit()
            else:
                layout_mode = layout_mode_err
        else:
            ok = 1
        rendered = self._renderLayout(layout_structure, ds,
                                      layout_mode=layout_mode, ok=ok, **kw)

        return rendered, ok, ds


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
        dm = self._getDataModel(None)
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout()
        layout.prepareLayoutWidgets(ds)
        if request is not None:
            ds.updateFromMapping(request.form)
        layout_structure = layout.computeLayoutStructure(layout_mode, dm)
        if validate:
            ok = layout.validateLayoutStructure(layout_structure, ds,
                                                layout_mode=layout_mode, **kw)
        else:
            ok = 1

        if validate and ok:
            # Check new entry id does not already exist
            # this hack works only if id is not computed by createEntry
            # XXX Hack, this should be done by field/schema... XXX
            id = dm.data[self.id_field]
            if id and self.hasEntry(id):
                ok = 0
                ds.setError(self.id_field, 'cpsdir_err_entry_already_exists')

        if validate and ok:
            # Creation...
            # Compute new id.
            id = dm.data[self.id_field]
            #entry = self._getEntryFromDataModel(dm)
            # XXX
            entry = dm.data.copy() # Need full entry not filtered by ACLs
            self.checkCreateEntryAllowed(id=id, entry=entry)
            try:
                new_id = self.createEntry(entry)
            except KeyError, e:
                msg = str(e)
                if msg.find('already exists') > 0:
                    # XXX Hack, this should be done by field/schema... XXX
                    ok = 0
                    ds.setError(self.id_field,
                                'cpsdir_err_entry_already_exists')
                else:
                    raise

            if ok:
                if new_id is not None and id != new_id:
                    # new id computed by createEntry
                    id = new_id
                    dm.data[self.id_field] = id

                # Redirect/render
                created_func = getattr(self, created_callback, None)
                if created_func is None:
                    raise ValueError("Unknown created_callback %s" %
                                     created_callback)
                rendered = created_func(ds) or ''

        if not validate or not ok:
            rendered = self._renderLayout(layout_structure, ds,
                                          layout_mode=layout_mode, ok=ok, **kw)
        return rendered, ok, ds

    security.declarePublic('renderSearchDetailed')
    def renderSearchDetailed(self, request=None, validate=0,
                             layout_mode='search', callback=None,
                             **kw):
        """Rendering for search.

        Calls callback when data has been validated.
        """
        dm = self._getSearchDataModel()
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout(search=1)
        layout.prepareLayoutWidgets(ds)
        if request is not None:
            ds.updateFromMapping(request.form)
        layout_structure = layout.computeLayoutStructure(layout_mode, dm)
        if validate:
            ok = layout.validateLayoutStructure(layout_structure, ds,
                                                layout_mode=layout_mode, **kw)
        else:
            ok = 1
        if validate and ok:
            # Call callback.
            callback_func = getattr(self, callback, None)
            if callback_func is None:
                raise ValueError("Unknown callback '%s'" % callback)
            rendered, ok = callback_func(self, ds, **kw)
            if not rendered:
                rendered = ''
        else:
            rendered = self._renderLayout(layout_structure, ds,
                                          layout_mode=layout_mode, ok=ok, **kw)
        return rendered, ok, ds

    #
    # Management API
    #


    #
    # Internal
    #

    security.declarePrivate('_getSchemas')
    def _getSchemas(self, search=0):
        """Get the schemas for this directory.

        If search=1, get the schemas for a search.

        Returns a sequence of Schema objects.
        """
        stool = getToolByName(self, 'portal_schemas')
        schemas = []
        if not search:
            schema_ids = [self.schema]
        else:
            if self.schema_search:
                schema_ids = [self.schema_search]
            else:
                schema_ids = [self.schema]
        for schema_id in schema_ids:
            schema = stool._getOb(schema_id, None)
            if schema is None:
                raise ValueError("Missing schema '%s' for directory  '%s'"
                                 % (schema_id, self.getId()))
            schemas.append(schema)
        return schemas

    security.declarePrivate('_getFieldIds')
    def _getFieldIds(self, search=0):
        """Get the fields ids by querying the schemas."""
        keys = []
        for schema in self._getSchemas(search=search):
            keys.extend(schema.keys())
        return keys

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry.

        If search is true, return the search adapters.
        Passes additional **kw to the adapters.
        """
        raise NotImplementedError

    security.declarePrivate('_getAdditionalRoles')
    def _getAdditionalRoles(self, id):
        """Get additional user roles provided to ACLs.

        The default implementation returns no additional roles.

        XXX merge this into the Entry Local Roles concept...
        """
        return ()

    security.declarePrivate('_getDataModel')
    def _getDataModel(self, id, check_acls=1, **kw):
        """Get the datamodel for an entry.

        Passes additional **kw to _getAdapters.
        """
        adapters = self._getAdapters(id, **kw)
        dm = DataModel(None, adapters, context=self)
        if not check_acls:
            dm._check_acls = 0 # XXX use API
        dm._fetch()
        if check_acls:
            # Now compute add_roles for entry
            # XXX merge additionalRoles and entry_local_roles
            entry = self._getEntryFromDataModel(dm)
            add_roles = self._getAdditionalRoles(id) # XXX what if id is dn ?
            entry_local_roles = self.getEntryLocalRoles(entry)
            add_roles = tuple(add_roles) + tuple(entry_local_roles)
            dm._setAddRoles(add_roles)
        return dm

    security.declarePrivate('_getSearchDataModel')
    def _getSearchDataModel(self):
        """Get the datamodel for a search rendering."""
        adapters = self._getAdapters(None, search=1)
        dm = DataModel(None, adapters, context=self)
        dm._check_acls = 0 # XXX use API
        dm._fetch()
        return dm

    security.declarePrivate('_getLayout')
    def _getLayout(self, search=0):
        """Get the layout for our type.

        If search=1, get the search layout.
        """
        ltool = getToolByName(self, 'portal_layouts')
        if not search:
            layout_id = self.layout
        else:
            if self.layout_search:
                layout_id = self.layout_search
            else:
                layout_id = self.layout
        layout = ltool._getOb(layout_id, None)
        if layout is None:
            raise ValueError("No layout '%s' for directory '%s'"
                             % (layout_id, self.getId()))
        return layout

    security.declarePrivate('_renderLayout')
    def _renderLayout(self, layout_structure, datastructure, **kw):
        """Render a layout according to the defined style.

        Uses the directory as a rendering context.
        """
        layout = layout_structure['layout']
        # Render layout structure.
        layout.renderLayoutStructure(layout_structure, datastructure, **kw)
        # Apply layout style.
        context = self
        rendered = layout.renderLayoutStyle(layout_structure, datastructure,
                                            context, **kw)
        return rendered

    #
    # Entry Local Roles
    #

    security.declarePrivate('getEntryLocalRoles')
    def getEntryLocalRoles(self, entry):
        """Get the effective entry local roles for an entry.

        Returns the list of roles whose condition evaluates to true.
        """
        res = []
        if not self.entry_roles:
            return res
        expr_context = self._createEntryLocalRoleExpressionContext(entry)
        for role, e, compiled in self.entry_roles:
            if not compiled:
                continue
            if compiled(expr_context):
                res.append(role)
        return res

    def _createEntryLocalRoleExpressionContext(self, entry):
        """Create an expression context for entry local roles conditions."""
        user = getSecurityManager().getUser()
        user_id = user.getId()
        entry_id = entry.get(self.id_field)
        # Get user entry lazily.
        if self.getId() == 'members' and entry_id == user_id:
            # Our own entry, just reuse it and avoid potential recursion.
            def getUserEntry(entry=entry):
                return entry
        else:
            # Get our entry from the members directory.
            mdir = getToolByName(self, 'portal_directories').members
            def getUserEntry(mdir=mdir, user_id=user_id):
                try:
                    return mdir._getEntry(user_id)
                except KeyError:
                    # We're not a member...
                    return {}
        mapping = {}
        # Put None values by default for all schema items.
        for field_id in self._getSchemas()[0].keys():
            mapping[field_id] = None
        # Put filled-in entry items in the namespace.
        mapping.update(entry)
        # Add basic namespace.
        mapping.update({
            'entry': entry,
            'entry_id': entry_id,
            'user': user,
            'user_id': user_id,
            'getUserEntry': getUserEntry,
            'portal': getToolByName(self, 'portal_url').getPortalObject(),
            'DateTime': DateTime,
            'nothing': None,
            })
        return getEngine().getContext(mapping)

    security.declareProtected(ManagePortal, 'listEntryLocalRoles')
    def listEntryLocalRoles(self):
        """List entry local roles.

        Returns a list of tuples (role, expr).
        """
        l = self.entry_roles
        entry_roles = [(r, e) for (r, e, c) in l]
        return entry_roles

    security.declareProtected(ManagePortal, 'addEntryLocalRole')
    def addEntryLocalRole(self, role, expr):
        """Add an entry local role.

        Returns '' if no error, 'exists' if the role already exists, or
        the error text if a compilatione error occured.
        """
        # Test if already exists.
        if [None for v in self.entry_roles if v[0] == role]:
            return 'exists'
        expr = expr.strip()
        if expr:
            try:
                compiled = Expression(expr)
            except CompilerError, e:
                return str(e)
        else:
            compiled = None
        self.entry_roles = self.entry_roles + [(role, expr, compiled)]
        return ''

    security.declareProtected(ManagePortal, 'delEntryLocalRole')
    def delEntryLocalRole(self, role):
        """Del an entry local role."""
        self.entry_roles = [v for v in self.entry_roles
                            if v[0] != role]

    security.declareProtected(ManagePortal, 'changeEntryLocalRole')
    def changeEntryLocalRole(self, role, expr):
        """Change an entry local role.

        Returns '' if no error, or the error text if a compilation
        error occured.
        """
        expr = expr.strip()
        if expr:
            try:
                compiled = Expression(expr)
            except CompilerError, e:
                return str(e)
        else:
            compiled = None
        new_v = (role, expr, compiled)
        self.entry_roles = [(v[0] == role and new_v or v)
                            for v in self.entry_roles]
        return ''

    #
    # ZMI
    #
    manage_options = (
        SimpleItemWithProperties.manage_options[:1] + (
        {'label': 'Entry Local Roles', 'action':'manage_entryLocalRoles'},) +
        SimpleItemWithProperties.manage_options[1:]+
        ({'label': 'Search','action': 'manage_searchDirectoryForm'},
         {'label': 'Export','action': 'manage_export'},
         ))
    security.declareProtected(ManagePortal, 'manage_entryLocalRoles')
    manage_entryLocalRoles = DTMLFile('zmi/manageEntryLocalRoles', globals())

    security.declareProtected(ManagePortal, 'manage_searchDirectoryForm')
    manage_searchDirectoryForm = DTMLFile('zmi/directory_search', globals())

    security.declareProtected(ManagePortal, 'manage_export')
    manage_export = DTMLFile('zmi/basedirectory_export', globals())

    security.declareProtected(ManagePortal, 'manage_searchDirectory')
    def manage_searchDirectory(self, mapping):
        """Search an entry (ZMI).

        Returns the results, and a list of field ids to display.
        """
        mapping['return_fields'] = ['*']
        res = self.searchEntries(**mapping)
        return res

    security.declareProtected(ManagePortal, 'manage_getZMISearchFields')
    def manage_getZMISearchFields(self):
        """Find which fields we can easily search from ZMI."""
        infos = []
        for schema in self._getSchemas(search=1):
            for field_id, field in schema.items():
                mt = field.meta_type
                if mt in ('CPS String Field',
                          'CPS String List Field'):
                    infos.append({'field_id': field_id,
                                  'field_type': mt,
                                  })
        return infos

    security.declareProtected(ManagePortal, 'manage_addEntryLocalRole')
    def manage_addEntryLocalRole(self, role, expr, REQUEST):
        """Add an entry local role (ZMI)."""
        res = self.addEntryLocalRole(role, expr)
        kw = {'role': role, 'expr': expr}
        if not res:
            msg = "Added."
            kw = {}
        elif res == 'exists':
            msg = "Error: Role Entry '%s' already exists." % role
        else:
            msg = "Error: " + res
        kw['manage_tabs_message'] = msg
        args = urlencode(kw)
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_entryLocalRoles?'+args)

    security.declareProtected(ManagePortal, 'manage_delEntryLocalRole')
    def manage_delEntryLocalRole(self, role, REQUEST):
        """Delete an entry local role (ZMI)."""
        self.delEntryLocalRole(role)
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_entryLocalRoles'
                                  '?manage_tabs_message=Deleted.')

    security.declareProtected(ManagePortal, 'manage_changeEntryLocalRole')
    def manage_changeEntryLocalRole(self, role, expr, REQUEST):
        """Change an entry local role (ZMI)."""
        res = self.changeEntryLocalRole(role, expr)
        if not res:
            msg = "Changed."
        else:
            msg = "Error: " + res
        args = urlencode({'manage_tabs_message': msg})
        # XXX should redisplay erroneous expression.
        REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_entryLocalRoles?'+args)

InitializeClass(BaseDirectory)
