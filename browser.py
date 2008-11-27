# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
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

import sys
from zLOG import LOG, INFO
import_ldap_ok = True
try:
     import ldap
except ImportError, err:
     if sys.exc_info()[2].tb_next is not None:
         # ImportError was caused deeper
         raise
     import_ldap_ok = False
     msg = "python-ldap is not installed, no LDAP support will be available"
     LOG("CPSDirectory.browser", INFO, msg)

from Products.CPSUtil.browser import BaseAddView
from Products.CPSSchemas.browser import BaseVocabularyAddView

from Products.CPSDirectory.MembersDirectory import MembersDirectory
from Products.CPSDirectory.GroupsDirectory import GroupsDirectory
from Products.CPSDirectory.RolesDirectory import RolesDirectory
from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
from Products.CPSDirectory.SQLDirectory import SQLDirectory
if import_ldap_ok:
    from Products.CPSDirectory.LDAPBackingDirectory import LDAPBackingDirectory
    from Products.CPSDirectory.LDAPServerAccess import LDAPServerAccess
from Products.CPSDirectory.MetaDirectory import MetaDirectory
from Products.CPSDirectory.StackingDirectory import StackingDirectory
from Products.CPSDirectory.LocalDirectory import LocalDirectory
from Products.CPSDirectory.IndirectDirectory import IndirectDirectory

from Products.CPSDirectory.DirectoryVocabulary import DirectoryVocabulary
from Products.CPSDirectory.DirectoryEntryVocabulary import (
    DirectoryEntryVocabulary)
from Products.CPSDirectory.IndirectDirectoryVocabulary import (
    IndirectDirectoryVocabulary)
if import_ldap_ok:
    from Products.CPSDirectory.LDAPDirectoryVocabulary import (
        LDAPDirectoryVocabulary)


class BaseDirectoryAddView(BaseAddView):
    """Base add view for a directory.
    """
    _dir_name = 'directories'
    description = u"A directory holds tabular information."

class MembersDirectoryAddView(BaseDirectoryAddView):
    """Add view for MembersDirectory."""
    klass = MembersDirectory

class GroupsDirectoryAddView(BaseDirectoryAddView):
    """Add view for GroupsDirectory."""
    klass = GroupsDirectory

class RolesDirectoryAddView(BaseDirectoryAddView):
    """Add view for RolesDirectory."""
    klass = RolesDirectory

class ZODBDirectoryAddView(BaseDirectoryAddView):
    """Add view for ZODBDirectory."""
    klass = ZODBDirectory

class SQLDirectoryAddView(BaseDirectoryAddView):
    """Add view for SQLDirectory."""
    klass = SQLDirectory

if import_ldap_ok:
    class LDAPBackingDirectoryAddView(BaseDirectoryAddView):
        """Add view for LDAPBackingDirectory."""
        klass = LDAPBackingDirectory

    class LDAPServerAccessAddView(BaseAddView):
         """Add view for LDAPServerAccess."""
         _dir_name = 'directories'
         klass = LDAPServerAccess
         description = u"LDAP Server Access hold connection and bind params."


class MetaDirectoryAddView(BaseDirectoryAddView):
    """Add view for MetaDirectory."""
    klass = MetaDirectory

class StackingDirectoryAddView(BaseDirectoryAddView):
    """Add view for StackingDirectory."""
    klass = StackingDirectory

class LocalDirectoryAddView(BaseDirectoryAddView):
    """Add view for LocalDirectory."""
    klass = LocalDirectory

class IndirectDirectoryAddView(BaseDirectoryAddView):
    """Add view for IndirectDirectory."""
    klass = IndirectDirectory


class DirectoryVocabularyAddView(BaseVocabularyAddView):
    """Add view for DirectoryVocabulary."""
    klass = DirectoryVocabulary

class DirectoryEntryVocabularyAddView(BaseVocabularyAddView):
    """Add view for DirectoryEntryVocabulary."""
    klass = DirectoryEntryVocabulary

class IndirectDirectoryVocabularyAddView(BaseVocabularyAddView):
    """Add view for IndirectDirectoryVocabulary."""
    klass = IndirectDirectoryVocabulary

if import_ldap_ok:
    class LDAPDirectoryVocabularyAddView(BaseVocabularyAddView):
        """Add view for LDAPDirectoryVocabulary."""
        klass = LDAPDirectoryVocabulary
