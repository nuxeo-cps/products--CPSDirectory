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

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties

from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure


class BaseDirectory(SimpleItemWithProperties):
    """Base Directory.

    A directory holds information about entries and how to access and
    display them.
    """

    meta_type = None

    security = ClassSecurityInfo()

    _properties = SimpleItemWithProperties._properties + (
        {'id': 'schema', 'type': 'string', 'mode': 'w',
         'label': 'Schema'},
        {'id': 'layout', 'type': 'string', 'mode': 'w',
         'label': 'Layout'},
        {'id': 'layout_style_prefix', 'type': 'string', 'mode': 'w',
         'label': 'Layout style prefix'},
        )

    schema = ''
    layout = ''
    layout_style_prefix = ''

    def __init__(self, id, **kw):
        self.id = id

    #
    # Usage API
    #

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.
        """
        raise NotImplementedError

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        raise NotImplementedError

    security.declarePublic('searchEntry')
    def searchEntry(self, **kw):
        """Search for entries in the directory.
        """
        raise NotImplementedError

    security.declarePublic('writeEntry')
    def writeEntry(self, entry):
        """Write an entry in the directory.
        """
        raise NotImplementedError

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
    def renderEntryDetailed(self, id, mode='view', **kw):
        """Render the entry.

        Returns (rendered, datastructure):
        - rendered is the rendered HTML,
        - datastructure is the resulting datastructure.
        """
        dm = self._getDataModel(id)
        ds = DataStructure(datamodel=dm)
        layout = self._getLayout(self.layout)
        layoutdata = layout.getLayoutData(ds)
        rendered = self._renderLayoutStyle(mode, layout=layoutdata,
                                           datastructure=ds, **kw)
        return rendered, ds

    #
    # Management API
    #


    #
    # Internal
    #

    security.declarePrivate('_getSchemas')
    def _getSchemas(self):
        """Get the schemas for this directory.

        Returns a sequence of Schema objects.
        """
        stool = getToolByName(self, 'portal_schemas')
        schemas = []
        for schema_id in [self.schema]:
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

    security.declarePrivate('_getDataModel')
    def _getDataModel(self, id):
        """Get the datamodel for an entry."""
        adapters = self._getAdapters(id)
        dm = DataModel(None, adapters)
        dm._fetch()
        return dm

    security.declarePrivate('_getLayout')
    def _getLayout(self, ob=None):
        """Get the layout for our type.
        """
        ltool = getToolByName(self, 'portal_layouts')
        layout_id = self.layout
        layout = ltool._getOb(layout_id, None)
        if layout is None:
            raise ValueError("No layout '%s' for directory '%s'"
                             % (layout_id, self.getId()))
        return layout

    security.declarePrivate('_renderLayoutStyle')
    def _renderLayoutStyle(self, mode, **kw):
        """Render a layout according to the defined style.

        Uses the directory as a rendering context.
        """
        layout_meth = self.layout_style_prefix + mode
        layout_style = getattr(self, layout_meth, None)
        if layout_style is None:
            raise RuntimeError("No layout method '%s'" % layout_meth)
        return layout_style(mode=mode, **kw)

InitializeClass(BaseDirectory)
