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

import re

from types import ListType, TupleType, StringType
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DateTime.DateTime import DateTime
from OFS.Image import File, Image

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter
from Products.CPSSchemas.BasicFields import CPSStringListField, CPSDateTimeField

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

def _isinstance(ob, cls):
    try:
        return isinstance(ob, cls)
    except TypeError:
        # In python 2.1 isinstance() raises TypeError
        # instead of returning 0 for ExtensionClasses.
        return 0


class LDAPDirectory(BaseDirectory):
    """LDAP Directory.

    A directory that connects to an LDAP server.

    This directory has two special fields, 'dn' and 'base_dn'.

    - 'dn' is always read-only.

    - 'base_dn' is read-only except during creation where it can be used
    to specify a subbranch.
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
        {'id': 'ldap_scope', 'type': 'selection', 'mode': 'w',
         'label': 'LDAP scope', 'select_variable': 'all_ldap_scopes'},
        {'id': 'ldap_search_classes', 'type': 'string', 'mode': 'w',
         'label': 'LDAP object classes (search)'},
        {'id': 'ldap_bind_dn', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind dn'},
        {'id': 'ldap_bind_password', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind password'},
        {'id': 'ldap_rdn_attr', 'type': 'string', 'mode': 'w',
         'label': 'LDAP rdn attribute (create)'},
        {'id': 'ldap_object_classes', 'type': 'string', 'mode': 'w',
         'label': 'LDAP object classes (create)'},
        )

    id_field = 'cn'
    title_field = 'cn'

    ldap_server = ''
    ldap_port = 389
    ldap_use_ssl = 0
    ldap_base = ''
    ldap_scope = 'ONELEVEL'
    ldap_search_classes = 'person'
    ldap_bind_dn = ''
    ldap_bind_password = ''
    ldap_rdn_attr = 'cn'
    ldap_object_classes = 'top, person'

    ldap_scope_c = ldap.SCOPE_SUBTREE
    ldap_search_classes_c = ['person']
    ldap_object_classes_c = ['top', 'person']

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
        self.ldap_scope_c = conv.get(self.ldap_scope, ldap.SCOPE_BASE)
        # Split classes
        classes = self.ldap_search_classes
        classes = [x.strip() for x in classes.split(',')]
        self.ldap_search_classes_c = filter(None, classes)
        self.ldap_search_classes = ', '.join(self.ldap_search_classes_c)
        classes = self.ldap_object_classes
        self.ldap_object_classes_c = [x.strip() for x in classes.split(',')]
        self.ldap_object_classes = ', '.join(self.ldap_object_classes_c)
        # Update delegate
        login_attr = '' # Not used
        rdn_attr = '' # Not used
        binduid_usage = 1 # 0=never, 1=always (on connect)
        read_only = 0
        self._delegate.edit(login_attr, self.ldap_base, rdn_attr,
                            self.ldap_object_classes_c,
                            self.ldap_bind_dn, self.ldap_bind_password,
                            binduid_usage, read_only)
        self._delegate.deleteServers([0])
        self._delegate.addServer(self.ldap_server, self.ldap_port,
                                 self.ldap_use_ssl)

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, id_is_dn=0):
        """Get the adapters for an entry."""
        dir = self
        adapters = [LDAPStorageAdapter(schema, id, dir, id_is_dn=id_is_dn)
                    for schema in self._getSchemas()]
        return adapters

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        return self.searchEntries()

    security.declarePrivate('listEntryDNs')
    def listEntryDNs(self):
        """List all the entry dns.

        This is LDAP-specific and assumes that 'dn' is in the schema.
        """
        res = self.searchEntries(return_fields=['dn'])
        return [data['dn'] for id, data in res]

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

    security.declarePrivate('listEntryDNsAndTitles')
    def listEntryDNsAndTitles(self):
        """List all the entry dns and titles.

        This is LDAP-specific and assumes that 'dn' is in the schema.
        """
        title_field = self.title_field
        res = self.searchEntries(return_fields=['dn', title_field])
        return [(data['dn'], data[title_field]) for id, data in res]

    security.declarePrivate('getEntryByDN')
    def getEntryByDN(self, dn):
        """Get entry filtered by acls and processes.

        This is LDAP-specific and assumes that 'dn' is in the schema.
        """
        dn = re.sub(r',\s+', ',', dn)
        if not (','+dn).endswith(','+self.ldap_base):
            raise ValueError("DN '%s' must be under '%s'" %
                             (dn, self.ldap_base))
        return self._getEntryKW(dn, id_is_dn=1)

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
        return self._hasEntry(id)

    security.declarePrivate('hasEntryByDN')
    def hasEntryByDN(self, dn):
        """Does the directory have a given entry?

        This is LDAP-specific.
        """
        dn = re.sub(r',\s+', ',', dn)
        if not (','+dn).endswith(','+self.ldap_base):
            raise ValueError("DN '%s' must be under '%s'" %
                             (dn, self.ldap_base))
        return self._hasEntry(dn, id_is_dn=1)

    security.declarePrivate('_hasEntry')
    def _hasEntry(self, id, id_is_dn=0):
        """Does the directory have a given entry?"""
        id_attr = self.id_field
        if id_is_dn or id_attr == 'dn':
            base = id
            scope = ldap.SCOPE_BASE
            filter = '(objectClass=*)'
        else:
            base = self.ldap_base
            scope = self.ldap_scope_c
            filter = ('(&%s%s)' % (self.objectClassFilter(),
                                   filter_format('(%s=%s)', (id_attr, id))))
        res = self._delegate.search(base=base,
                                    scope=scope,
                                    filter=filter,
                                    attrs=[id_attr])
        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            return 0

        return res['size'] != 0

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory.

        If a base_dn attribute is present, it is used to decide which
        subbranch to use.
        """
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
        rdn_attr = self.ldap_rdn_attr
        rdn = '%s=%s' % (rdn_attr, entry[rdn_attr])
        # XXX check rdn value syntax better...
        if ',' in rdn:
            raise ValueError("Illegal character ',' in rdn %s" % rdn)
        base = self.ldap_base
        # Maybe create in a subbranch.
        base_dn = entry.get('base_dn', '').strip()
        if base_dn:
            base_dn = re.sub(r',\s+', ',', base_dn)
            if not (','+base_dn).endswith(','+base):
                raise ValueError("Base DN must be under %s" % base)
            base = base_dn
        attrs = self._makeAttrsFromData(entry)
        attrs['objectClass'] = self.ldap_object_classes_c
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
        # Make attributes. Skip ignore_attrs.
        attrs = {}
        for field_id, field in self._getSchemas()[0].items(): # XXX
            if field.write_ignore_storage:
                continue
            value = data[field_id]
            if field_id in ('dn', 'base_dn'):
                # Never modifiable directly.
                continue
            if field_id in ignore_attrs:
                continue
            if not value:
                continue # Skip empty values
            # Convert field data to strings for LDAP
            if _isinstance(value, Image) or _isinstance(value, File):
                value = str(value.data)
            elif _isinstance(value, DateTime):
                # The nicer ways of converting to strings does not work with
                # dates before 1970.
                # LDAP generalized time strongly recommends GMT, so it
                # should be converted. But if a date is stored, ignore
                # the timezone:
                if value.Time() != "00:00:00":
                    value = value.toZone('GMT')
                value = '%d%02d%02d%02d%02d%02dZ' % (value.year(),
                    value.month(), value.day(), value.hour(), value.minute(),
                    value.second())

            # LDAP wants everything as lists
            if type(value) not in (ListType, TupleType):
                value = [value]
            attrs[field_id] = value
        return attrs

    def _getLDAPEntry(self, id, field_ids=['dn'], id_is_dn=0):
        """Get LDAP entry for a user."""
        id_attr = self.id_field
        if id_is_dn or id_attr == 'dn':
            base = id
            scope = ldap.SCOPE_BASE
            filter = '(objectClass=*)'
        else:
            base = self.ldap_base
            scope = self.ldap_scope_c
            filter = ('(&%s%s)' % (self.objectClassFilter(),
                                   filter_format('(%s=%s)', (id_attr, id))))

        res = self._delegate.search(base=base,
                                    scope=scope,
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
                                    scope=self.ldap_scope_c,
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
        classes = self.ldap_search_classes_c
        if classes:
            res = ''.join(['(objectClass=%s)' % each
                           for each in classes])
            if len(classes) > 1:
                res = '(|%s)' % res
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

    def __init__(self, schema, id, dir, field_ids=None, id_is_dn=0):
        """Create an Adapter for a schema.

        If id_is_dn is true, then the passed id is actually a dn.
        This is used to get an entry by its dn.
        """
        self._id = id
        self._dir = dir
        self._id_is_dn = id_is_dn
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
        entry = self._dir._getLDAPEntry(id, field_ids=field_ids,
                                        id_is_dn=self._id_is_dn)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        if field_id == 'dn':
            return entry['dn']
        elif field_id == 'base_dn':
            dn = entry['dn']
            return dn[dn.find(',')+1:].strip()
        if not entry.has_key(field_id):
            return field.getDefault()
        field_data = entry[field_id]
        if _isinstance(field, CPSStringListField):
            return field_data
        if _isinstance(field, CPSDateTimeField):
            # strptime is not available on Windows, so do this the
            # hard way:
            time = field_data[0]
            year = int(time[0:4])
            month = int(time[4:6])
            day = int(time[6:8])
            hour = int(time[8:10])
            minute = int(time[10:12])
            second = int(time[12:14])
            # Timezones are in ISO spec. Examples:
            # GMT: 'Z'
            # CET: '+0100'
            # EST: '-0600'
            tz = time[14:]
            if tz[0] in ('+', '-'): # There is a timezone specified.
                tz = 'GMT' + tz
            else:
                tz = 'GMT'
            value = DateTime(year, month, day, hour, minute, second, tz)
            # Convert to local zone for correct display?
            value = value.toZone(value.localZone())
            return  value

        return '; '.join(field_data) # Join multivalued fields.

    def _setData(self, data, **kw):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, **kw)

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
