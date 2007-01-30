# Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
from OFS.SimpleItem import Item
from OFS.Folder import Folder

class FakeRoot(Folder):
    id = ''
    def getPhysicalRoot(self):
        return self

class FakeDirectoryTool(Folder):
    id = 'portal_directories'

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


