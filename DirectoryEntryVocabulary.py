# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Julien Anguenot <ja@nuxeo.com>
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
"""Directory Entry Vocabulary

This vocabulary is built by looking for an entry, defined by entry_id, within a
directory.  The vocabulary is an element of the entry defined by voc_entry_id.

In here, the key and the items are the same for convenience.

You may use DirectoryEntryVocabulary with whatever sort of directory (LDAP or
whatever)
"""

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import View

from DirectoryVocabulary import DirectoryVocabulary

class DirectoryEntryVocabulary(DirectoryVocabulary):
    """Directory Entry Vocabulary

    This vocabulary is built by looking for an entry, defined by entry_id,
    within a directory.  The vocabulary is an element of the entry defined by
    voc_entry_id.

    In here, the key and the items are the same for convenience.

    You may use DirectoryEntryVocabulary with whatever sort of directory (LDAP
    or whatever)
    """

    meta_type = "CPS Directory Entry Vocabulary"

    security = ClassSecurityInfo()

    _properties = DirectoryVocabulary._properties + (
        {'id': 'entry_id', 'type': 'string', 'mode': 'w',
         'label': 'Entry ID'},
        {'id': 'voc_entry_field', 'type': 'string', 'mode': 'w',
         'label': 'Vocabulary entry field'},
        )

    entry_id = ''
    voc_entry_field = ''

    security.declareProtected(View, '__getitem__')
    def __getitem__(self, key):
        if self.add_empty_key and key == '':
            return self.empty_key_value
        dir = self._getDirectory()
        entry = dir._getEntryKW(self.entry_id, field_ids=[self.voc_entry_field])
        voc = entry.get(self.voc_entry_field, None)
        if voc is not None and key in voc:
            return key
        else:
            raise KeyError

    security.declareProtected(View, 'keys')
    def keys(self):
        dir = self._getDirectory()
        voc = dir.getEntry(self.entry_id, None)
        res = voc.get(self.voc_entry_field, [])

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
        keys = self.keys()
        res = []
        for key in keys:
          res.append((key, key))

        # XXX self.keys() already adds empty key
        # we just need here to add empty_key_value
        if self.add_empty_key:
            v = ('',self.empty_key_value)
            if self.empty_key_pos == 'first':
                res[0] = v
            else:
                res[-1] =  v
        return res

    security.declareProtected(View, 'has_key')
    def has_key(self, key):
        if self.add_empty_key and key == '':
            return 1
        return key in self.keys()

InitializeClass(DirectoryEntryVocabulary)
