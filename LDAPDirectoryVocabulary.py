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
"""LDAPDirectoryVocabulary.

Vocabulary referencing an LDAP directory, and using its DN as a key.
"""

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import View
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties


class LDAPDirectoryVocabulary(SimpleItemWithProperties):
    """LDAP Directory Vocabulary

    This vocabulary is built by listing all the entries of a directory.

    The keys are the entry DNS, and the values are the entry titles.
    """

    meta_type = "CPS LDAP Directory Vocabulary"

    security = ClassSecurityInfo()

    _properties = (
        {'id': 'title', 'type': 'string', 'mode': 'w',
         'label': 'Title'},
        {'id': 'title_msgid', 'type': 'string', 'mode': 'w',
         'label': 'Title Msgid'},
        {'id': 'description', 'type': 'text', 'mode': 'w',
         'label':'Description'},
        {'id': 'directory', 'type': 'string', 'mode': 'w',
         'label':'LDAP Directory'},
        )

    title = ''
    title_msgid = ''
    description = ''
    directory = ''

    def __init__(self, id, **kw):
        self.id = id
        self.manage_changeProperties(**kw)

    def _getDirectory(self):
        """Get the directory referenced."""
        dirtool = getToolByName(self, 'portal_directories')
        return getattr(dirtool, self.directory)

    security.declareProtected(View, '__getitem__')
    def __getitem__(self, key):
        dir = self._getDirectory()
        return dir.getEntryByDN(key)[dir.title_field]

    security.declareProtected(View, 'get')
    def get(self, key, default=None):
        try:
            return self[key]
        except (KeyError, AttributeError):
            return default

    security.declareProtected(View, 'getMsgid')
    def getMsgid(self, key, default=None):
        # XXX dummy
        return key+'msgid'

    security.declareProtected(View, 'keys')
    def keys(self):
        dir = self._getDirectory()
        return dir.listEntryDNs()

    security.declareProtected(View, 'items')
    def items(self):
        dir = self._getDirectory()
        return dir.listEntryDNsAndTitles()

    security.declareProtected(View, 'values')
    def values(self):
        return [t[1] for t in self.items()]

    security.declareProtected(View, 'has_key')
    def has_key(self, key):
        dir = self._getDirectory()
        return dir.hasEntryByDN(key)

InitializeClass(LDAPDirectoryVocabulary)