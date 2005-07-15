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
"""Directory widget types.

Definition of directory-related widget types.
"""

from zLOG import LOG, DEBUG, TRACE
from urllib import urlencode
from cgi import escape
from Globals import InitializeClass
from types import StringType, ListType, TupleType

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.WidgetTypesTool import WidgetTypeRegistry
from Products.CPSSchemas.Widget import CPSWidgetType
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import \
     CPSSelectWidget, CPSMultiSelectWidget, CPSIdentifierWidget


class EntryMixin:
    """Mixin class that knows how to access id and title from
    and entry, even if it's LDAP keyed by dn.
    """

    def getIdAndTitle(self, value):
        """Get id and title from an entry value.

        Returns a tuple (id, title), or None, None if the
        entry could not be found.
        """
        portal_directories = getToolByName(self, 'portal_directories')
        dir = getattr(portal_directories, self.directory)
        # If value is None or empty, do not query directories
        if not value:
            id = None
            title = None
        else:
            if self.entry_type == 'id':
                id = value
                try:
                    title = dir.getEntry(id, default=None)[dir.title_field]
                except (IndexError, ValueError, KeyError, TypeError, AttributeError):
                    title = None
            else: # entry_type == 'dn':
                try:
                    entry = dir.getEntryByDN(value)
                except (IndexError, ValueError, KeyError):
                    id = None
                    title = None
                else:
                    id = entry[dir.id_field]
                    title = entry[dir.title_field]
        return (id, title)

    def getTagForValue(self, value):
        id, title = self.getIdAndTitle(value)
        if id is None or title is None:
            return renderHtmlTag('span', contents=escape('? (%s)' % value))
        portal_url = getToolByName(self, 'portal_url')()
        if self.directory_view:
            directory = self.directory_view
        else:
            directory = self.directory
        href = '%s/%s?%s' % (portal_url, self.skin_name,
                             urlencode({'dirname': directory, 'id': id,}))
        return renderHtmlTag('a', href=href, contents=escape(title))


##################################################

class CPSDirectoryEntryWidget(CPSSelectWidget, EntryMixin):
    """Directory entry widget.

    This widget displays a reference to a single directory entry as an
    href link.

    In edit mode it uses a SelectWidget for now. XXX
    """
    meta_type = "CPS Directory Entry Widget"

    _properties = CPSSelectWidget._properties + (
        {'id': 'directory', 'type': 'string', 'mode': 'w',
         'label': 'Directory', 'is_required' : 1},
        {'id': 'directory_view', 'type': 'string', 'mode': 'w',
         'label': 'Optional directory used in view mode'},
        {'id': 'entry_type', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_entry_types',
         'label': 'Entry type'},
        {'id': 'skin_name', 'type': 'string', 'mode': 'w',
         'label': 'Skin name'},
        {'id': 'popup_mode', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_popup_modes',
         'label': 'browse or search'},
        )
    all_entry_types = ['id', 'dn']
    all_popup_modes = ['browse', 'search']

    directory = ''
    directory_view = ''
    entry_type = all_entry_types[0]
    skin_name = 'cpsdirectory_entry_view'
    popup_mode = all_popup_modes[0]

    def prepare(self, datastructure, **kw):
        """Prepare datastructure from datamodel."""
        datamodel = datastructure.getDataModel()
        value = datamodel[self.fields[0]]
        if isinstance(value, (ListType, TupleType)):
            LOG('CPSDirectoryEntryWidget.prepare', TRACE,
                'expected String got Typle %s use first element' % value)
            if len(value):
                value = value[0]
            else:
                value = ''
        datastructure[self.getWidgetId()] = value
        datastructure[self.getWidgetId() + '_set'] = ''

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        widget_id = self.getWidgetId()
        widget_set_id = widget_id + '_set'
        if not self.is_required and not datastructure[widget_set_id]:
            datamodel = datastructure.getDataModel()
            datamodel[self.fields[0]] = ''
            datastructure[widget_id] = ''
            return 1
        return CPSSelectWidget.validate(self, datastructure, **kw)

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        render_method = 'widget_directoryentry_render'
        meth = getattr(self, render_method, None)
        if meth is None:
            raise RuntimeError("Unknown Render Method %s for widget type %s"
                               % (render_method, self.getId()))
        value = datastructure[self.getWidgetId()]

        if mode == 'view':
            render = ''
            if value:
                render = self.getTagForValue(value)
            return meth(mode=mode, value=value, render=render)
        elif mode == 'edit':
            portal_directories = getToolByName(self, 'portal_directories')
            dir = getattr(portal_directories, self.directory)
            display_attr = dir.title_field
            id, title = self.getIdAndTitle(value)

            if value:
                jsvalue = value.replace("'", "\\'")
                jsvalue = jsvalue.replace('"', '\\"')
            else:
                jsvalue = ''

            return meth(mode=mode, value=value, jsvalue=jsvalue, title=title,
                        display_attr=display_attr)

InitializeClass(CPSDirectoryEntryWidget)


class CPSDirectoryEntryWidgetType(CPSWidgetType):
    """Directory entry widget type."""
    meta_type = "CPS Directory Entry Widget Type"
    cls = CPSDirectoryEntryWidget

InitializeClass(CPSDirectoryEntryWidgetType)

##################################################

class CPSDirectoryMultiEntriesWidget(CPSMultiSelectWidget, EntryMixin):
    """Directory multi-entries widget.

    This widget displays a reference to a several directory entries as
    an href links.

    In edit mode it uses a MultiSelectWidget for now. XXX
    """
    meta_type = "CPS Directory MultiEntries Widget"

    _properties = CPSMultiSelectWidget._properties + (
        {'id': 'directory', 'type': 'string', 'mode': 'w',
         'label': 'Directory', 'is_required' : 1},
        {'id': 'root_uid', 'type': 'string', 'mode': 'w',
         'label': 'id of the root if the directory is hierarchical'},
        {'id': 'directory_view', 'type': 'string', 'mode': 'w',
         'label': 'Optional directory used in view mode'},
        {'id': 'entry_type', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_entry_types',
         'label': 'Entry type'},
        {'id': 'skin_name', 'type': 'string', 'mode': 'w',
         'label': 'Skin name'},
        {'id': 'separator', 'type': 'string', 'mode': 'w',
         'label': 'display separator in view mode' },
        {'id': 'popup_mode', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_popup_modes',
         'label': 'Popup mode'},
        )
    all_entry_types = ['id', 'dn']
    all_popup_modes = ['browse', 'search', 'none']
    directory = ''
    root_uid = ''
    directory_view = ''
    entry_type = all_entry_types[0]
    skin_name = 'cpsdirectory_entry_view'
    popup_mode = all_popup_modes[0]
    separator = ', '

    def prepare(self, datastructure, **kw):
        """Prepare datastructure from datamodel."""
        datamodel = datastructure.getDataModel()
        value = datamodel[self.fields[0]]
        if isinstance(value, StringType):
            LOG('CPSDirectoryMultiEntriesWidget.prepare', TRACE,
                'expected List got String %s converting into list' % value)
            if value:
                value = ['value',]
            else:
                value = []
        datastructure[self.getWidgetId()] = value

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        err = None
        v = []
        widget_id = self.getWidgetId()
        value = datastructure[widget_id]
        if not isinstance(value, (ListType, TupleType)):
            err = 'cpsschemas_err_multiselect'
        else:
            vocabulary = self._getVocabulary(datastructure)
            for i in value:
                try:
                    i = str(i)
                except ValueError:
                    err = 'cpsschemas_err_multiselect'
                    break
                if i == 'directorymultientries_reset':
                    continue
                if not vocabulary.has_key(i):
                    err = 'cpsschemas_err_multiselect'
                    break
                v.append(i)
        datastructure[widget_id] = v
        if err:
            datastructure.setError(widget_id, err)
        else:
            datamodel = datastructure.getDataModel()
            datamodel[self.fields[0]] = v

        return not err

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        render_method = 'widget_directorymultientries_render'
        meth = getattr(self, render_method, None)
        if meth is None:
            raise RuntimeError("Unknown Render Method %s for widget type %s"
                               % (render_method, self.getId()))
        portalDirectories = getToolByName(self, 'portal_directories')
        try:
            dir = getattr(portalDirectories, self.directory)
        except AttributeError:
            err = 'Directory %s not available' % self.directory
            raise RuntimeError(err)

        value = datastructure[self.getWidgetId()]
        if value:
            # sorting here because some storage (LDAP user group)
            # doesn't store ordered list
            value = list(value)
            value.sort()
        if mode == 'view':
            render = ''
            if value is not None:
                res = [self.getTagForValue(v) for v in value]
                render = self.separator.join(res)
            return meth(mode=mode, value=value, render=render)
        elif mode == 'edit':
            if value is None:
                value = []
            if (self.popup_mode == 'none'):
                return CPSMultiSelectWidget.render(self, mode, datastructure, **kw)
            display_attr = dir.title_field
            ids_and_titles = [(v, self.getIdAndTitle(v)[1]) for v in value]
            return meth(mode=mode, values=value, ids_and_titles=ids_and_titles,
                        display_attr=display_attr)

InitializeClass(CPSDirectoryMultiEntriesWidget)


class CPSDirectoryMultiEntriesWidgetType(CPSWidgetType):
    """Directory entry widget type."""
    meta_type = "CPS Directory MultiEntries Widget Type"
    cls = CPSDirectoryMultiEntriesWidget

InitializeClass(CPSDirectoryMultiEntriesWidgetType)

##################################################

class CPSUserIdentifierWidget(CPSIdentifierWidget):
    """Identifier widget."""
    meta_type = "CPS User Identifier Widget"

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        widget_id = self.getWidgetId()
        err, v = self._extractValue(datastructure[widget_id])
        if not err and v and not self._checkIdentifier(v):
            err = 'cpsschemas_err_identifier'

        if err:
            datastructure.setError(widget_id, err)
            datastructure[widget_id] = v
        else:
            datamodel = datastructure.getDataModel()
            datamodel[self.fields[0]] = v
            if kw['layout_mode'] == 'create':
                portal_registration = getToolByName(self, 'portal_registration')
                return portal_registration.isMemberIdAllowed(v)

        return not err

InitializeClass(CPSUserIdentifierWidget)

class CPSUserIdentifierWidgetType(CPSWidgetType):
    """User Identifier Widget Type."""
    meta_type = "CPS User Identifier Widget Type"
    cls = CPSUserIdentifierWidget

InitializeClass(CPSUserIdentifierWidgetType)

##################################################

WidgetTypeRegistry.register(CPSDirectoryEntryWidgetType,
                            CPSDirectoryEntryWidget)
WidgetTypeRegistry.register(CPSDirectoryMultiEntriesWidgetType,
                            CPSDirectoryMultiEntriesWidget)
WidgetTypeRegistry.register(CPSUserIdentifierWidgetType,
                            CPSUserIdentifierWidget)
