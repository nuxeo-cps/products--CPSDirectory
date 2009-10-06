# Copyright 2005-2007 Nuxeo SAS <http://nuxeo.com>
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
"""Various fake CPS objects for testing
"""
import sys
from types import UnicodeType
from copy import deepcopy
from OFS.SimpleItem import Item
from OFS.Folder import Folder

class FakeRoot(Folder):
    id = ''
    def getPhysicalRoot(self):
        return self

class FakeDirectoryTool(Folder):
    id = 'portal_directories'

class FakeUserFolder(Folder):
    USERS_DIRECTORY_ID = 'members'
    id = 'acl_users'
    def getProperty(self, property_id):
        if 'users_dir':
            return self.USERS_DIRECTORY_ID
        else:
            return property_id

class FakeMembershipTool(Folder):
    id = 'portal_membership'
    def deleteMembers(self, member_ids, delete_memberareas=1,
                      delete_localroles=0, check_permission=1):
        pass

default_encoding = sys.getdefaultencoding()
if default_encoding == 'ascii':
    default_encoding = 'iso-8859-15'
def toUTF8(s):
    if not isinstance(s, UnicodeType):
        s = unicode(s, default_encoding)
    return s.encode('utf-8')
def fromUTF8(s):
    return unicode(s, 'utf-8').encode(default_encoding)

class FakeField:
    def __init__(self, id='', read_expr=None, read_dep=()):
        self.read_expr = read_expr
        self.read_process_dependent_fields = read_dep
        self.id = id
    write_process_expr = ''
    write_process_dependent_fields = ()
    write_ignore_storage = False
    read_ignore_storage = False
    def getDefault(self, datamodel=None):
        return ''
    def processValueAfterRead(self, value, *args):
        if self.read_expr is not None:
            return self.read_expr(value, *args)
        return value
    def processValueBeforeWrite(self, value, *args):
        return value
    def checkReadAccess(self, *args):
        pass
    def checkWriteAccess(self, *args):
        pass
    def computeDependantFields(self, *args, **kw):
        pass
    def _getAllDependantFieldIds(self):
        return ()
    def convertToLDAP(self, value):
        return [toUTF8(str(value))]
    def convertFromLDAP(self, values):
        return fromUTF8(values[0])
    def manage_fixupOwnershipAfterAdd(self):
        pass
    def manage_afterAdd(self, x, y):
        pass
    def getId(self):
        return self.id
    def _setId(self, id):
        self.id = id

class FakeListField(FakeField):
    def getDefault(self, datamodel=None):
        return []
    def convertToLDAP(self, value):
        return [toUTF8(str(v)) for v in value]
    def convertFromLDAP(self, values):
        return [fromUTF8(v) for v in values]

class FakeSchema(Item):
    def __init__(self, fields):
        self.fields = fields
    def keys(self):
        return self.fields.keys()
    def items(self):
        return self.fields.items()
    def values(self):
        return self.fields.values()
    def __getitem__(self, key):
        return self.fields[key]
    def _setObject(self, id_, object_):
        if id_ not in self.fields.keys():
            self.fields[id_] = object_
        raise KeyError(
            "The id '%s' is invalid - it is already in use." %(id_))

_marker = object()
class FakeSchemasTool(Folder):
    id = 'portal_schemas'
    def _getOb(self, id, default=_marker):
        if default is _marker:
            return getattr(self, id)
        else:
            return getattr(self, id, default)

#
# Fake directories (useful for non meta/stacking/etc.)
#

_marker = object()
class FakeDirectory(Folder):
    def __init__(self, id, id_field, blank):
        self._setId(id)
        Folder.__init__(self)
        self.id_field = id_field
        self.blank = blank
        self.entries = {}
    def setFieldIds(self, field_ids):
        self.field_ids = field_ids
    def _getFieldIds(self):
        return self.field_ids
    def getEntry(self, id, default=_marker):
        try:
            return self.entries[id]
        except KeyError:
            if default is _marker:
                raise
            else:
                return default
    _getEntry = getEntry
    _getEntryKW = getEntry
    def createEntry(self, entry):
        new = deepcopy(self.blank)
        new.update(entry)
        self.entries[entry[self.id_field]] = new
    _createEntry = createEntry
    def editEntry(self, entry):
        self.entries[entry[self.id_field]].update(entry)
    _editEntry = editEntry
    def deleteEntry(self, id):
        del self.entries[id]
    _deleteEntry = deleteEntry
    def hasEntry(self, id):
        return self.entries.has_key(id)
    _hasEntry = hasEntry
    def listEntryIds(self):
        return self.entries.keys()
    def searchEntries(self, return_fields=None, **kw):
        res = []
        # find entries
        for eid, entry in self.entries.items():
            for k, v in kw.items():
                # GR list behaviour expected from CPSUserFolder is alternatives
                # don't know if that's right (code wasn't tested before)
                # maybe too much LDAP oriented ?
                if (isinstance(v, list) and entry[k] in v) or \
                  entry[k] == v:
                    res.append((eid, entry))

        if return_fields is None:
            return [eid for eid, _ in res]
        if return_fields == ['*']:
            return res
        raise NotImplementedError
    _searchEntries = searchEntries

class FakeDirectoryNormalizing(FakeDirectory):
    """A simple normalization case: case independency"""

    password_field = None

    def __init__(self, *args, **kwargs):
        pw_field = kwargs.pop('password_field', None)
        if pw_field is not None:
            self.password_field = pw_field
        FakeDirectory.__init__(self, *args, **kwargs)

    def getEntry(self, id, default=_marker, **kw):
        for k, v in self.entries.items():
            if id.lower() == k.lower():
                return v
        else:
            if default is _marker:
                raise KeyError(id)
            else:
                return default
    _getEntry = getEntry
    _getEntryKW = getEntry

    def searchEntries(self, return_fields=None, **kw):
        # switch criteria to lowercase.
        crit = deepcopy(kw)
        for k, v in crit.items():
            if isinstance(v, list):
                crit[k] = [i.lower() for i in v]
            elif isinstance(v, basestring):
                crit[k] = v.lower()

        # find entries
        res = []
        for eid, entry in self.entries.items():
            for k, v in crit.items():
                # GR list behaviour expected from CPSUserFolder is alternatives
                # don't know if that's right (code wasn't tested before)
                # maybe too much LDAP oriented ?
                ev = entry[k].lower()
                if (isinstance(v, list) and ev in v) or ev == v:
                    res.append((eid, entry))

        if return_fields is None:
            return [eid for eid, _ in res]
        if return_fields == ['*']:
            return res
        raise NotImplementedError
    _searchEntries = searchEntries

    def getEntryAuthenticated(self, id, password, **kw):
        entry = self.getEntry(id)
        if password != entry[self.password_field]:
            raise AuthenticationFailed
        return entry

    def isAuthenticating(self):
        return bool(self.password_field)



