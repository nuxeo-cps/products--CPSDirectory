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
from cgi import escape
from urllib import urlencode
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.WidgetTypesTool import WidgetTypeRegistry
from Products.CPSSchemas.Widget import CPSWidgetType
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import CPSStringWidget

##################################################

class CPSDirectoryEntryWidget(CPSStringWidget):
    """Directory entry widget.

    This widget displays a reference to a directory entry as an href
    link.

    In edit mode XXX
    """
    meta_type = "CPS Directory Entry Widget"

    _properties = CPSStringWidget._properties + (
        {'id': 'dir_name', 'type': 'string', 'mode': 'w',
         'label': 'Directory name'},
        {'id': 'entry_type', 'type': 'selection', 'mode': 'w',
         'select_variable': 'all_entry_types',
         'label': 'Entry type'},
        {'id': 'dn_rdn_attr', 'type': 'string', 'mode': 'w',
         'label': 'DN: rdn attribute'},
        {'id': 'dn_base', 'type': 'string', 'mode': 'w',
         'label': 'DN: base'},
        )
    all_entry_types = ['direct', 'dn']

    dir_name = ''
    entry_type = all_entry_types[0]
    dn_rdn_attr = ''
    dn_base = ''

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""
        value = datastructure[self.getWidgetId()]
        if mode == 'view':
            if self.entry_type == 'direct':
                id = value
            else: # entry_type == 'dn':
                try:
                    # Get the rdn value
                    id = value.split(',')[0].split('=')[1].strip()
                except IndexError:
                    id = 'unknown'
            portal_url = getToolByName(self, 'portal_url')()
            portal_directories = getToolByName(self, 'portal_directories')
            dir = getattr(portal_directories, self.dir_name)
            # yyy
            skin_name = 'cpsdirectory_entry_view'
            href = '%s/%s?%s' % (portal_url, skin_name,
                                 urlencode({'dirname': self.dir_name,
                                            'id': id,
                                            }))
            contents = 'fooXXX' # quoted!
            return renderHtmlTag('a',
                                 href=href,
                                 contents=contents)
        elif mode == 'edit':
            # XXX should be a select widget.
            kw = {'type': 'text',
                  'name': self.getHtmlWidgetId(),
                  'value': value,
                  'size': self.display_width,
                  }
            if self.size_max:
                kw['maxlength'] = self.size_max
            return renderHtmlTag('input', **kw)
        raise RuntimeError('unknown mode %s' % mode)

InitializeClass(CPSDirectoryEntryWidget)


class CPSDirectoryEntryWidgetType(CPSWidgetType):
    """Directory entry widget type."""
    meta_type = "CPS Directory Entry Widget Type"
    cls = CPSDirectoryEntryWidget

InitializeClass(CPSDirectoryEntryWidgetType)


WidgetTypeRegistry.register(CPSDirectoryEntryWidgetType,
                            CPSDirectoryEntryWidget)
