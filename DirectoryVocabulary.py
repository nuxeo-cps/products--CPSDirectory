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
"""DirectoryReferenceVocabulary.

Vocabulary referencing a directory.
"""

from zLOG import LOG, DEBUG
from Globals import InitializeClass, DTMLFile
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import View, ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties

from Products.CPSSchemas.Vocabulary import CPSVocabulary


class DirectoryReferenceVocabulary(SimpleItemWithProperties):
    """Directory Reference Vocabulary

    This vocabulary is built by listing all the entries of a directory.
    """

    meta_type = "CPS Directory Reference Vocabulary"

    security = ClassSecurityInfo()

    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w',
         'label': 'Title'},
        {'id': 'title_msgid', 'type': 'string', 'mode': 'w',
         'label': 'Title Msgid'},
        {'id': 'description', 'type': 'text', 'mode': 'w',
         'label':'Description'},
        {'id': 'directory', 'type': 'string', 'mode': 'w',
         'label':'Directory'},
        )

    title = ''
    title_msgid = ''
    description = ''
    directory = ''

    def __init__(self, id, **kw):
        self.manage_changeProperties(**kw)

    def _getDirectory(self):
        """Get the directory referenced."""
        dirtool = getToolByName(self, 'portal_directories')
        return getattr(dirtool, self.directory)

    security.declareProtected(View, '__getitem__')
    def __getitem__(self, key):
        # XXX dummy
        return key

    security.declareProtected(View, 'get')
    def get(self, key, default=None):
        # XXX dummy
        return key

    security.declareProtected(View, 'getMsgid')
    def getMsgid(self, key, default=None):
        # XXX dummy
        return key+'msgid'

    security.declareProtected(View, 'keys')
    def keys(self):
        return self._getDirectory().listEntryIds()

    security.declareProtected(View, 'items')
    def items(self):
        # XXX dummy
        return [(x, x) for x in self.keys()]

    security.declareProtected(View, 'has_key')
    def has_key(self, key):
        # XXX dummy
        return key in self.keys()
