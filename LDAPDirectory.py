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
"""LDAPDirectory
"""

from zLOG import LOG, DEBUG, ERROR

from types import ListType, TupleType, StringType
from Globals import InitializeClass
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter

from Products.CPSDirectory.BaseDirectory import BaseDirectory

try:
    from Products.LDAPUserGroupsFolder.LDAPDelegate import \
         LDAPDelegate, ldap
    from Products.LDAPUserGroupsFolder.utils import filter_format
except ImportError:
    from Products.LDAPUserFolder.LDAPDelegate import \
         LDAPDelegate, ldap
    from Products.LDAPUserFolder.utils import filter_format

ldap_scopes = (ldap.SCOPE_BASE, ldap.SCOPE_ONELEVEL, ldap.SCOPE_SUBTREE)


_marker = []

NO_PASSWORD = '__NO_PASSWORD__'


class LDAPDirectory(BaseDirectory):
    """LDAP Directory.

    A directory that connects to an LDAP server.
    """

    meta_type = 'CPS LDAP Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'ldap_server', 'type': 'string', 'mode': 'w',
         'label': 'LDAP server'},
        {'id': 'ldap_port', 'type': 'int', 'mode': 'w',
         'label': 'LDAP port'},
        {'id': 'ldap_use_ssl', 'type': 'boolean', 'mode': 'w',
         'label': 'LDAP use ssl'},
        {'id': 'ldap_base', 'type': 'string', 'mode': 'w',
         'label': 'LDAP base'},
        {'id': 'ldap_scope_str', 'type': 'selection', 'mode': 'w',
         'label': 'LDAP scope', 'select_variable': 'all_ldap_scopes'},
        {'id': 'ldap_bind_dn', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind dn'},
        {'id': 'ldap_bind_password', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind password'},
        {'id': 'ldap_rdn_attr', 'type': 'string', 'mode': 'w',
         'label': 'LDAP rdn attribute'},
        {'id': 'ldap_object_classes_str', 'type': 'string', 'mode': 'w',
         'label': 'LDAP object classes'},
        )

    id_field = 'cn'
    title_field = 'cn'

    ldap_server = ''
    ldap_port = 389
    ldap_use_ssl = 0
    ldap_base = ''
    ldap_scope_str = 'BASE'
    ldap_bind_dn = ''
    ldap_bind_password = ''
    ldap_rdn_attr = 'cn'
    ldap_object_classes_str = 'top, person'

    ldap_scope = ldap.SCOPE_BASE
    ldap_object_classes = ['top', 'person']

    all_ldap_scopes = ('BASE', 'ONELEVEL', 'SUBTREE')

    def __init__(self, id, **kw):
        BaseDirectory.__init__(self, id, **kw)
        self._delegate = LDAPDelegate()
        self._delegate.addServer('')

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        BaseDirectory._postProcessProperties(self)
        # Convert string stuff
        conv = {'BASE': ldap.SCOPE_BASE,
                'ONELEVEL': ldap.SCOPE_ONELEVEL,
                'SUBTREE': ldap.SCOPE_SUBTREE,
                }
        self.ldap_scope = conv.get(self.ldap_scope_str, ldap.SCOPE_BASE)
        # Split classes
        classes = self.ldap_object_classes_str
        self.ldap_object_classes = [x.strip() for x in classes.split(',')]
        self.ldap_object_classes_str = ', '.join(self.ldap_object_classes)
        # Update delegate
        login_attr = '' # Not used
        rdn_attr = '' # Not used
        binduid_usage = 1 # 0=never, 1=always (on connect)
        read_only = 0
        self._delegate.edit(login_attr, self.ldap_base, rdn_attr,
                            self.ldap_object_classes,
                            self.ldap_bind_dn, self.ldap_bind_password,
                            binduid_usage, read_only)
        self._delegate.deleteServers([0])
        self._delegate.addServer(self.ldap_server, self.ldap_port,
                                 self.ldap_use_ssl)

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id):
        """Get the adapters for an entry."""
        dir = self
        adapters = [LDAPStorageAdapter(schema, id, dir)
                    for schema in self._getSchemas()]
        return adapters

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        return self._searchEntries()

    security.declarePublic('searchEntries')
    def searchEntries(self, **kw):
        """Search for entries in the directory.

        Keys with empty values are removed.
        Keys with value '*' search for an existing field.
        Otherwise do substring search.

        Returns a list of entry ids.
        """
        schemas = self._getSchemas()
        field_ids = []
        for schema in schemas:
            field_ids.extend(schema.keys())
        filter_elems = [self.objectClassFilter()]
        for key, value in kw.items():
            if not key in field_ids:
                continue
            if key == 'dn': # XXX treat it
                continue
            if not value:
                continue
            if value == '*':
                value = ''
            if isinstance(value, ListType) or isinstance(value, TupleType):
                pass
            elif isinstance(value, StringType):
                value = [value]
            else:
                raise ValueError("Bad value %s for '%s'" % `value`, key)
            fl = []
            for v in value:
                if v:
                    fv = filter_format('(%s=*%s*)', (key, v))
                else:
                    fv = filter_format('(%s=*)', (key,))
                fl.append(fv)
            f = ''.join(fl)
            if len(fl) > 1:
                f = '(|%s)' % f
            filter_elems.append(f)
        filter = ''.join(filter_elems)
        if len(filter_elems) > 1:
            filter = '(&%s)' % filter
        return self._searchEntries(filter=filter)

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        id_attr = self.id_field
        filter = ('(&%s(objectClass=*))' %
                  filter_format('(%s=%s)', (id_attr, id)))
        res = self._delegate.search(base=self.ldap_base,
                                    scope=self.ldap_scope,
                                    filter=filter,
                                    attrs=[id_attr])
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            return 0

        return res['size'] != 0

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed()
        if not entry.has_key(self.id_field):
            raise ValueError("Missing value for '%s' in entry" %
                             self.id_field)
        if not entry.has_key(self.ldap_rdn_attr):
            raise ValueError("Missing value for '%s' in entry" %
                             self.ldap_rdn_attr)
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise ValueError("Entry '%s' already exists" % id)
        # XXX check rdn value syntax...
        rdn_attr = self.ldap_rdn_attr
        rdn = '%s=%s' % (rdn_attr, entry[rdn_attr])
        base = self.ldap_base
        attrs = self._makeAttrsFromData(entry)
        attrs['objectClass'] = self.ldap_object_classes
        msg = self._delegate.insert(base=base, rdn=rdn, attrs=attrs)
        if msg:
            raise ValueError("LDAP error: %s" % msg)

    #
    # Internal
    #

    def _makeAttrsFromData(self, data, ignore_attrs=[]):
        # Make attributs. Skin rdn_attr
        attrs = {}
        for fieldid, field in self._getSchemas()[0].items(): # XXX
            value = data[fieldid]
            if fieldid == 'dn':
                # Never modifiable directly.
                continue
            if fieldid in ignore_attrs:
                continue
            if type(value) not in (ListType, TupleType):
                value = [value]
            attrs[fieldid] = value
        return attrs

    def _searchEntries(self, filter=None):
        """Search entries according to filter."""
        if not filter:
            filter = '(objectClass=*)'
        id_attr = self.id_field
        res = self._delegate.search(base=self.ldap_base,
                                    scope=self.ldap_scope,
                                    filter=filter,
                                    attrs=[id_attr])
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            return []
        else:
            results = res['results']
            if id_attr == 'dn':
                return [e['dn'] for e in results]
            else:
                return [e[id_attr][0] for e in results]

    def objectClassFilter(self):
        if self.ldap_object_classes:
            res = '(|'
            for each in self.ldap_object_classes:
                res += ' (objectClass=%s)' % each
            res += ')'
            return res
        else:
            return '(objectClass=*)'

InitializeClass(LDAPDirectory)


class LDAPStorageAdapter(BaseStorageAdapter):
    """LDAP Storage Adapter

    This adapter gets and sets data from an LDAP server.
    """

    def __init__(self, schema, id, dir):
        """Create an Adapter for a schema.
        """
        self._id = id
        self._dir = dir
        BaseStorageAdapter.__init__(self, schema)

    def _getEntry(self, field_ids=['dn']):
        """Get entry for current user."""
        dir = self._dir
        id = self._id
        # XXX treat case where id_field == 'dn' (use base=dn)
        # XXX use self.ldap_object_classes here too
        filter = '(&%s(objectClass=*))' % filter_format('(%s=%s)',
                                                        (dir.id_field, id))
        res = dir._delegate.search(base=dir.ldap_base,
                                   scope=dir.ldap_scope,
                                   filter=filter,
                                   attrs=field_ids)
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            raise ValueError(res['exception']) # XXX do better ?
        if not res['size']:
            raise ValueError("No user '%s'" % id)

        return res['results'][0]

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        if self._id is None:
            # Creation.
            return self.getDefaultData()

        entry = self._getEntry(self._schema.keys())

        data = {}
        for field_id, field in self._schema.items():
            if field_id == 'dn':
                value = entry['dn']
            else:
                if entry.has_key(field_id):
                    value = entry[field_id][0] # XXX multi-valued args!!!
                else:
                    value = field.getDefault()
            data[field_id] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        dir = self._dir

        # Get dn by doing a lookup on the current entry.
        user_dn = self._getEntry()['dn']

        # Find the rdn attr.
        rdn = user_dn.split(',')[0]
        rdn_attr, rdn_value = rdn.split('=', 1)

        # XXX treat change of rdn
        attrs = dir._makeAttrsFromData(data, ignore_attrs=[rdn_attr])

        if attrs:
            msg = dir._delegate.modify(user_dn, attrs=attrs)
            if msg.startswith('STRONG_AUTH_REQUIRED'):
                raise ValueError("Authentication required")
            elif msg:
                raise ValueError("LDAP error: %s" % msg)

InitializeClass(LDAPStorageAdapter)
