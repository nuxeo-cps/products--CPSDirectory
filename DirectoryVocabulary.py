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
"""DirectoryVocabulary.

Vocabulary referencing a directory.
"""

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.permissions import View, ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties

from Products.CPSSchemas.VocabulariesTool import VocabularyTypeRegistry

from zope.interface import implements
from Products.CPSSchemas.interfaces import IPropertyVocabulary


class DirectoryVocabulary(SimpleItemWithProperties):
    """Directory Vocabulary

    This vocabulary is built by listing all the entries of a directory.

    The keys are the entry ids, and the values are the entry titles.

    For LDAP directories, if 'Use DN as key' is checked, then the keys
    are the entry DNs instead of the entry ids.
    """

    implements(IPropertyVocabulary)

    meta_type = "CPS Directory Vocabulary"

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
        {'id': 'add_empty_key', 'type': 'boolean', 'mode': 'w',
         'label':'Add an empty key'},
        {'id': 'empty_key_pos', 'type': 'selection', 'mode': 'w',
         'select_variable': 'empty_key_pos_select',
         'label':'Empty key position'},
        {'id': 'empty_key_value', 'type': 'string', 'mode': 'w',
         'label':'Empty key value'},
        )

    title = ''
    title_msgid = ''
    description = ''
    directory = ''
    add_empty_key = 0
    empty_key_pos_select = ('first', 'last')
    empty_key_pos = empty_key_pos_select[0]
    empty_key_value = ''

    def __init__(self, id, **kw):
        self.id = id
        self.manage_changeProperties(**kw)

    def _getDirectory(self):
        """Get the directory referenced."""
        dirtool = getToolByName(self, 'portal_directories')
        return getattr(dirtool, self.directory)

    security.declareProtected(View, '__getitem__')
    def __getitem__(self, key):
        if self.add_empty_key and key == '':
            return self.empty_key_value
        dir = self._getDirectory()
        title_field = dir.title_field
        field_ids_d = {title_field: None}
        schema = dir._getUniqueSchema()
        dep_ids = schema[title_field].read_process_dependent_fields
        for dep_id in dep_ids:
            field_ids_d[dep_id] = None
        field_ids = field_ids_d.keys()
        entry = dir._getEntryKW(key, field_ids=field_ids)
        return entry[title_field]

    security.declareProtected(View, 'get')
    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, AttributeError):
            return default

    security.declareProtected(View, 'getMsgid')
    def getMsgid(self, key, default=''):
        """ Create a default msgid for the key """
        try:
            label = self[key]
        except (KeyError, AttributeError):
            label = str(default)
        return "label_cpsdir_"+ self.id + "_" + label

    security.declareProtected(View, 'keys')
    def keys(self):
        dir = self._getDirectory()
        res = dir.listEntryIds()
        if self.add_empty_key:
            v = ''
            res = list(res)
            if self.empty_key_pos == 'first':
                res.insert(0, v)
            else:
                res.append(v)
        return res

    security.declareProtected(View, 'items')
    def items(self):
        dir = self._getDirectory()
        res = dir.listEntryIdsAndTitles()
        if self.add_empty_key:
            v = ('', self.empty_key_value)
            res = list(res)
            if self.empty_key_pos == 'first':
                res.insert(0, v)
            else:
                res.append(v)
        return res

    security.declareProtected(View, 'values')
    def values(self):
        return [t[1] for t in self.items()]

    security.declareProtected(View, 'has_key')
    def has_key(self, key):
        if self.add_empty_key and key == '':
            return 1
        dir = self._getDirectory()
        return dir._hasEntry(key)

    security.declareProtected(ManagePortal, 'isUserModified')
    def isUserModified(self):
        """Tell if the vocabulary has been modified by a user.
        """
        return 0

InitializeClass(DirectoryVocabulary)

VocabularyTypeRegistry.register(DirectoryVocabulary)
