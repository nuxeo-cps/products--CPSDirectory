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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties

from Products.CPSSchemas.PropertiesPostProcessor import PropertiesPostProcessor
from Products.CPSSchemas.StorageAdapter import AttributeStorageAdapter
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.Field import ReadAccessError
from Products.CPSSchemas.Field import WriteAccessError


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
        {'id': 'acl_access_roles_str', 'type': 'string', 'mode': 'w',
         'label': "ACL: directory access roles"},
        {'id': 'acl_entry_create_roles_str', 'type': 'string', 'mode': 'w',
         'label': "ACL: directory create roles"},
        {'id': 'id_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry id'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        )

    schema = ''
    schema_search = ''
    layout = ''
    layout_search = ''
    acl_access_roles_str = 'Manager; Member'
    acl_entry_create_roles_str = 'Manager'
    id_field = ''
    title_field = ''

    acl_access_roles = ['Manager', 'Member']
    acl_entry_create_roles = ['Manager']

    def __init__(self, id, **kw):
        self.id = id

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        # Split on ',' or ';' or ' '.
        for attr_str, attr, seps in (
            ('acl_access_roles_str', 'acl_access_roles', ',; '),
            ('acl_entry_create_roles_str', 'acl_entry_create_roles', ',; '),
            ):
            v = [getattr(self, attr_str)]
            for sep in seps:
                vv = []
                for s in v:
                    vv.extend(s.split(sep))
                v = vv
            v = [s.strip() for s in v]
            v = filter(None, v)
            setattr(self, attr_str, '; '.join(v))
            setattr(self, attr, v)

    #
    # Usage API
    #

    security.declarePublic('isVisible')
    def isVisible(self):
        """Is the directory visible by the current user?"""
        return getSecurityManager().getUser().has_role(
            self.acl_access_roles)

    security.declarePublic('isCreateEntryAllowed')
    def isCreateEntryAllowed(self):
        """Check that user can create an entry.

        Returns a boolean.
        """
        return getSecurityManager().getUser().has_role(
            self.acl_entry_create_roles)

    security.declarePublic('checkCreateEntryAllowed')
    def checkCreateEntryAllowed(self):
        """Check that user can create an entry.

        Raises Unauthorized if not.
        """
        if not self.isCreateEntryAllowed():
            raise Unauthorized("No create access to directory")

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        raise NotImplementedError

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        raise NotImplementedError

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        raise NotImplementedError

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        dm = self._getDataModel(id)
        entry = {}
        for key in dm.keys():
            try:
                entry[key] = dm[key]
            except ReadAccessError:
                pass
        return entry

    security.declarePublic('searchEntries')
    def searchEntries(self, **kw):
        """Search for entries in the directory.

        Returns a list of entry ids. # XXX more attrs needed...
        """
        raise NotImplementedError

    security.declarePublic('writeEntry')
    def writeEntry(self, entry):
        """Write an entry in the directory.
        """
        id = entry[self.id_field]
        dm = self._getDataModel(id)
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
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout()
        layout.prepareLayoutWidgets(ds)
        mode_chooser = layout.getStandardWidgetModeChooser(layout_mode, ds)
        layout_structure = layout.computeLayoutStructure(ds, mode_chooser)
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
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout()
        layout.prepareLayoutWidgets(ds)
        if request is None:
            validate = 0
        else:
            validate = 1
            ds.updateFromMapping(request.form)
        mode_chooser = layout.getStandardWidgetModeChooser(layout_mode, ds)
        layout_structure = layout.computeLayoutStructure(ds, mode_chooser)
        if validate:
            ok = layout.validateLayoutStructure(layout_structure, ds,
                                                layout_mode=layout_mode, **kw)
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
        mode_chooser = layout.getStandardWidgetModeChooser(layout_mode, ds)
        layout_structure = layout.computeLayoutStructure(ds, mode_chooser)
        if validate:
            ok = layout.validateLayoutStructure(layout_structure, ds,
                                                layout_mode=layout_mode, **kw)
        else:
            ok = 1

        if validate and ok:
            # Check new entry id does not already exist
            # XXX should be done by field/schema... XXX
            id = dm.data[self.id_field]
            if self.hasEntry(id):
                ok = 0
                widget_id = 'widget__'+self.id_field # XXX hack!
                ds.setError(widget_id, 'cpsdirectory_err_entry_already_exists')

        if not validate or not ok:
            rendered = self._renderLayout(layout_structure, ds,
                                          layout_mode=layout_mode, ok=ok, **kw)
        else:
            # Creation...
            # Compute new id.
            id = dm.data[self.id_field]
            # XXX create
            entry = dm.data.copy()
            self.createEntry(entry)
            # Redirect/render
            created_func = getattr(self, created_callback, None)
            if created_func is None:
                raise ValueError("Unknown created_callback %s" %
                                 created_callback)
            rendered = created_func(ds) or ''

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
        mode_chooser = layout.getStandardWidgetModeChooser(layout_mode, ds)
        layout_structure = layout.computeLayoutStructure(ds, mode_chooser)
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
            rendered, ok = callback_func(self, ds)
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
                raise RuntimeError("Missing schema '%s' for directory  '%s'"
                                   % (schema_id, self.getId()))
            schemas.append(schema)
        return schemas

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        raise NotImplementedError

    security.declarePrivate('_getAdditionalRoles')
    def _getAdditionalRoles(self, id):
        """Get additional user roles provided to ACLs."""
        return ()

    security.declarePrivate('_getDataModel')
    def _getDataModel(self, id):
        """Get the datamodel for an entry."""
        adapters = self._getAdapters(id)
        add_roles = self._getAdditionalRoles(id)
        dm = DataModel(None, adapters, context=self, add_roles=add_roles)
        dm._fetch()
        return dm


    security.declarePrivate('_getSearchAdapters')
    def _getSearchAdapters(self):
        return [AttributeStorageAdapter(schema, None)
                for schema in self._getSchemas(search=1)]

    security.declarePrivate('_getSearchDataModel')
    def _getSearchDataModel(self):
        """Get the datamodel for a search rendering."""
        adapters = self._getSearchAdapters()
        dm = DataModel(None, adapters, context=self)
        dm._check_acls = 0 # XXX
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

InitializeClass(BaseDirectory)
