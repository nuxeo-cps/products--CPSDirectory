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

from zLOG import LOG, DEBUG
from urllib import urlencode
from cgi import escape
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.WidgetTypesTool import WidgetTypeRegistry
from Products.CPSSchemas.Widget import CPSWidgetType
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import CPSSelectWidget
from Products.CPSSchemas.BasicWidgets import CPSMultiSelectWidget



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
        if self.entry_type == 'id':
            id = value
            try:
                title = dir.getEntry(id)[dir.title_field]
            except (IndexError, ValueError, KeyError):
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
        if id is None:
            id = 'unknown'
        if title is None:
            title = '? (%s)' % value
        portal_url = getToolByName(self, 'portal_url')()
        href = '%s/%s?%s' % (portal_url, self.skin_name,
                             urlencode({'dirname': self.directory,
                                        'id': id,
                                        }))
        return renderHtmlTag('a',
                             href=href,
                             contents=escape(title))


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
         'label': 'Directory'},
        {'id': 'entry_type', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_entry_types',
         'label': 'Entry type'},
        {'id': 'skin_name', 'type': 'string', 'mode': 'w',
         'label': 'Skin name'},
        )
    all_entry_types = ['id', 'dn']

    directory = ''
    entry_type = all_entry_types[0]
    skin_name = 'cpsdirectory_entry_view'

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        value = datastructure[self.getWidgetId()]
        if mode == 'view':
            if value:
                return self.getTagForValue(value)
            else:
                return ''
        elif mode == 'edit':
            return CPSDirectoryEntryWidget.inheritedAttribute('render')(
                self, mode, datastructure, **kw)
        raise RuntimeError('unknown mode %s' % mode)

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
         'label': 'Directory'},
        {'id': 'entry_type', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_entry_types',
         'label': 'Entry type'},
        {'id': 'skin_name', 'type': 'string', 'mode': 'w',
         'label': 'Skin name'},
        )
    all_entry_types = ['id', 'dn']

    directory = ''
    entry_type = all_entry_types[0]
    skin_name = 'cpsdirectory_entry_view'

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        value = datastructure[self.getWidgetId()]
        if mode == 'view':
            res = [self.getTagForValue(v) for v in value]
            return ', '.join(res)
        elif mode == 'edit':
            return CPSDirectoryMultiEntriesWidget.inheritedAttribute(
                'render')(self, mode, datastructure, **kw)
        raise RuntimeError('unknown mode %s' % mode)

InitializeClass(CPSDirectoryMultiEntriesWidget)


class CPSDirectoryMultiEntriesWidgetType(CPSWidgetType):
    """Directory entry widget type."""
    meta_type = "CPS Directory MultiEntries Widget Type"
    cls = CPSDirectoryMultiEntriesWidget

InitializeClass(CPSDirectoryMultiEntriesWidgetType)

##################################################

WidgetTypeRegistry.register(CPSDirectoryEntryWidgetType,
                            CPSDirectoryEntryWidget)
WidgetTypeRegistry.register(CPSDirectoryMultiEntriesWidgetType,
                            CPSDirectoryMultiEntriesWidget)
