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
from OFS.Image import File, Image

from Products.CMFCore.utils import getToolByName

# XXX we must not depend on CPSCore ! XXX
from Products.CPSCore.utils import _isinstance

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter
from Products.CPSSchemas.BasicFields import CPSStringListField

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
        {'id': 'ldap_search_classes_str', 'type': 'string', 'mode': 'w',
         'label': 'LDAP object classes (search)'},
        {'id': 'ldap_bind_dn', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind dn'},
        {'id': 'ldap_bind_password', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind password'},
        {'id': 'ldap_rdn_attr', 'type': 'string', 'mode': 'w',
         'label': 'LDAP rdn attribute (create)'},
        {'id': 'ldap_object_classes_str', 'type': 'string', 'mode': 'w',
         'label': 'LDAP object classes (create)'},
        )

    id_field = 'cn'
    title_field = 'cn'

    ldap_server = ''
    ldap_port = 389
    ldap_use_ssl = 0
    ldap_base = ''
    ldap_scope_str = 'ONELEVEL'
    ldap_search_classes_str = 'person'
    ldap_bind_dn = ''
    ldap_bind_password = ''
    ldap_rdn_attr = 'cn'
    ldap_object_classes_str = 'top, person'

    ldap_scope = ldap.SCOPE_SUBTREE
    ldap_search_classes = ['person']
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
        classes = self.ldap_search_classes_str
        classes = [x.strip() for x in classes.split(',')]
        self.ldap_search_classes = filter(None, classes)
        self.ldap_search_classes_str = ', '.join(self.ldap_search_classes)
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
        return self.searchEntries()

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles."""
        title_field = self.title_field
        if self.id_field == title_field:
            res = self.searchEntries()
            return [(id, id) for id in res]
        else:
            res = self.searchEntries(return_fields=[title_field])
            return [(id, data[title_field]) for id, data in res]

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.

        LDAP specifics:
        - Returns all entries if query is empty.
        - Keys with empty values are removed.
        - Keys with value '*' search for an existing field.
        - Otherwise does substring search.
        """
        schema = self._getSchemas()[0]
        all_field_ids = schema.keys()
        # Find attrs needed to compute returned fields.
        if return_fields is None:
            attrs = None
        else:
            attrsd = {}
            if return_fields == ['*']:
                return_fields = all_field_ids
            for field_id in return_fields:
                if field_id not in all_field_ids:
                    continue
                attrsd[field_id] = None
                dep_ids = schema[field_id].read_process_dependent_fields
                for dep_id in dep_ids:
                    attrsd[dep_id] = None
            attrs = attrsd.keys()
        # Build filter
        filter_elems = [self.objectClassFilter()]
        LOG('searchEntries', DEBUG, 'search query is %s' % `kw`)
        for key, value in kw.items():
            if not key in all_field_ids:
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
                raise ValueError("Bad value %s for '%s'" % (`value`, key))
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
        return self._searchEntries(filter=filter, return_attrs=attrs)

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

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed()
        user_dn = self._getLDAPEntry(id)['dn']
        msg = self._delegate.delete(dn=user_dn)
        if msg:
            raise ValueError("LDAP error: %s" % msg)

    #
    # Internal
    #

    def _getAdapterForPartialData(self, attrs):
        """Get an adapter for partial data."""
        dir = self
        schema = self._getSchemas()[0]
        adapter = LDAPStorageAdapter(schema, None, dir, field_ids=attrs)
        return adapter

    def _getPartialDataModel(self, adapter, entry):
        """Get a partial datamodel representing the entry.

        entry is the LDAP entry returned from the delegate.
        """
        data = adapter._getData(entry=entry)
        return data

    def _makeAttrsFromData(self, data, ignore_attrs=[]):
        # Make attributes. Skip rdn_attr
        attrs = {}
        for field_id, field in self._getSchemas()[0].items(): # XXX
            if field.write_ignore_storage:
                continue
            value = data[field_id]
            if field_id == 'dn':
                # Never modifiable directly.
                continue
            if field_id in ignore_attrs:
                continue
            if not value:
                continue # Skip empty values
            # Convert field data to strings for LDAP
            if _isinstance(value, Image) or _isinstance(value, File):
                value = str(value.data)
            # LDAP wants everything as lists
            if type(value) not in (ListType, TupleType):
                value = [value]
            attrs[field_id] = value
        return attrs

    def _getLDAPEntry(self, id, field_ids=['dn']):
        """Get LDAP entry for a user."""
        # XXX treat case where id_field == 'dn' (use base=dn)
        # XXX use self.ldap_search_classes here too
        filter = '(&%s(objectClass=*))' % filter_format('(%s=%s)',
                                                        (self.id_field, id))
        res = self._delegate.search(base=self.ldap_base,
                                    scope=self.ldap_scope,
                                    filter=filter,
                                    attrs=field_ids)
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            raise ValueError(res['exception']) # XXX do better ?
        if not res['size']:
            raise ValueError("No user '%s'" % id)

        return res['results'][0]

    def _searchEntries(self, filter=None, return_attrs=None):
        """Search entries according to filter."""
        if not filter:
            filter = '(objectClass=*)'
        id_attr = self.id_field
        if return_attrs is None:
            attrs = [id_attr]
        else:
            attrs = list(return_attrs)
            if id_attr not in return_attrs:
                attrs.append(id_attr)
        LOG('_searchEntries', DEBUG, 'filter=%s attrs=%s' % (filter, attrs))
        res = self._delegate.search(base=self.ldap_base,
                                    scope=self.ldap_scope,
                                    filter=filter,
                                    attrs=attrs)
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            return []

        # Now we must compute a partial datamodel for each result,
        # to get correct computed fields.

        results = res['results']
        if return_attrs is None:
            if id_attr == 'dn':
                return [e['dn'] for e in results]
            else:
                return [e[id_attr][0] for e in results]
        else:
            adapter = self._getAdapterForPartialData(return_attrs)
            datas = []
            for e in results:
                data = self._getPartialDataModel(adapter, e)
                datas.append((e, data))
            if id_attr == 'dn':
                return [(e['dn'], data) for e, data in datas]
            else:
                return [(e[id_attr][0], data) for e, data in datas]

    security.declarePrivate('objectClassFilter')
    def objectClassFilter(self):
        classes = self.ldap_search_classes
        if classes:
            res = ''.join(['(objectClass=%s)' % each
                           for each in classes])
            if len(classes) > 1:
                res ='(|%s)' % res
            return res
        else:
            return '(objectClass=*)'

    def getImageFieldData(self, entry_id, field_id, REQUEST, RESPONSE):
        """Gets the raw data from a non ZODB image field"""
        entry = self.getEntry(entry_id)
        field = entry[field_id]
        if type(field) is StringType:
            field = Image(entry_id, '', field)
        return field.index_html(REQUEST, RESPONSE)

InitializeClass(LDAPDirectory)


class LDAPStorageAdapter(BaseStorageAdapter):
    """LDAP Storage Adapter

    This adapter gets and sets data from an LDAP server.
    """

    def __init__(self, schema, id, dir, field_ids=None):
        """Create an Adapter for a schema.
        """
        self._id = id
        self._dir = dir
        BaseStorageAdapter.__init__(self, schema, field_ids=field_ids)

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        if id is None:
            # Creation.
            return self.getDefaultData()
        # Compute entry so that it is passed as kw to _getFieldData.
        field_ids = [field_id for field_id, field in self.getFieldItems()]
        entry = self._dir._getLDAPEntry(id, field_ids)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        print "_getFieldData", field
        if not entry.has_key(field_id):
            return field.getDefault()
        if field_id == 'dn':
            return entry['dn']
        field_data = entry[field_id]
        if _isinstance(field, CPSStringListField):
            return field_data
        return '; '.join(field_data) # Join multivalued fields.

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)
        for field_id, field in self._field_items:
            if field.write_ignore_storage:
                del data[field_id]

        # Get dn by doing a lookup on the current entry.
        user_dn = self._dir._getLDAPEntry(self._id)['dn']

        # Find the rdn attr.
        rdn = user_dn.split(',')[0]
        rdn_attr, rdn_value = rdn.split('=', 1)

        # XXX treat change of rdn

        dir = self._dir
        attrs = dir._makeAttrsFromData(data, ignore_attrs=[rdn_attr])
        if attrs:
            msg = dir._delegate.modify(user_dn, attrs=attrs)
            if msg.startswith('STRONG_AUTH_REQUIRED'):
                raise ValueError("Authentication required")
            elif msg:
                raise ValueError("LDAP error: %s" % msg)

    def _getContentUrl(self, entry_id, field_id):
        return '%s/getImageFieldData?entry_id=%s&field_id=%s' % (
            self._dir.absolute_url(), entry_id, field_id)


InitializeClass(LDAPStorageAdapter)
