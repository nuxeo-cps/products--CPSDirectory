# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Author: Anahide Tchertchian <at@nuxeo.com>
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
"""IndirectDirectoryVocabulary.

Vocabulary listing all the accepted entries within an indirect directory.
"""

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.CMFCorePermissions import View, ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import SimpleItemWithProperties

from DirectoryVocabulary import DirectoryVocabulary

class IndirectDirectoryVocabulary(DirectoryVocabulary):
    """Indirect Directory Vocabulary

    This vocabulary is built by listing all the accepted entries of an indirect
    directory.

    The keys are the entry ids, and the values are the entry titles.

    """

    meta_type = "CPS Indirect Directory Vocabulary"

    security = ClassSecurityInfo()

    security.declareProtected(View, 'items')
    def items(self):
        # this is the only change
        res = self.listAllPossibleEntriesIdsAndTitles()
        if self.add_empty_key:
            v = ('', self.empty_key_value)
            res = list(res)
            if self.empty_key_pos == 'first':
                res.insert(0, v)
            else:
                res.append(v)
        return res

InitializeClass(IndirectDirectoryVocabulary)
