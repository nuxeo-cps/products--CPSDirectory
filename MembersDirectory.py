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
"""MembersDirectory
"""

from zLOG import LOG, DEBUG

from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory


_marker = []


class MembersDirectory(BaseDirectory):
    """Members Directory.

    A directory that know how to deal with members.
    """

    meta_type = 'CPS Members Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'id_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for id'},
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for password'},
        {'id': 'roles_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for roles'},
        {'id': 'groups_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for groups'},
        {'id': 'title_field', 'type': 'string', 'mode': 'w',
         'label': 'Field for entry title'},
        )

    id_field = 'id'
    password_field = 'password'
    roles_field = 'roles'
    groups_field = 'groups'
    title_field = 'id'

    security.declarePrivate('getAdapters')
    def getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [MemberStorageAdapter(schema, id, dir)
                    for schema in self.getSchemas()]
        return adapters

    security.declarePublic('getEntry')
    def getEntry(self, id):
        """Get entry filtered by acls and processes.
        """
        return {
            'id': id,
            'givenName': 'Raoul',
            'sn': id.upper(),
            }

InitializeClass(MembersDirectory)


class MemberStorageAdapter(BaseStorageAdapter):
    """Members Storage Adapter

    This adapter gets and sets data from the user folder and the member
    data.
    """

    def __init__(self, schema, id, dir):
        """Create an Adapter for a schema.

        The id passed is the member id.
        """
        self._id = id
        self._dir = dir
        self._mtool = getToolByName(dir, 'portal_membership')
        BaseStorageAdapter.__init__(self, schema)

    def _delete(self, field_id):
        raise NotImplementedError

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        dir = self._dir
        member = self._mtool.getMemberById(id)
        if member is None:
            raise KeyError("No member '%s'" % id)
        if not hasattr(aq_base(member), 'getMemberId'):
            raise KeyError("User '%s' is not a member" % id)
        user = member.getUser()
        data = {}
        for fieldid, field in self._schema.items():
            if fieldid == dir.id_field:
                value = id
            elif fieldid == dir.password_field:
                value = 'this is the password XXX'
            elif fieldid == dir.roles_field:
                value = user.getRoles()
            elif fieldid == dir.groups_field:
                if hasattr(aq_base(user), 'getGroups'):
                    value = user.getGroups()
                else:
                    value = () # XXX or field.getDefault() ?
            else:
                value = member.getProperty(fieldid, _marker)
                if value is _marker:
                    value = field.getDefault()
            data[fieldid] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        raise NotImplementedError
        for field_id in self._schema.keys():
            setattr(self._ob, field_id, data[field_id])

InitializeClass(MemberStorageAdapter)
