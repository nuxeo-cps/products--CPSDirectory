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
"""LDAPBackingDirectory

This is a simple but efficient version of an LDAP Directory.
It has no dependencies besides the ldap module.

In this directory the id is always the dn.
"""

from zLOG import LOG, DEBUG, TRACE, ERROR

import re
import sys
from types import ListType, TupleType, StringType, IntType, UnicodeType
import ldap
from ldap.filter import filter_format
from ldap import SCOPE_BASE, SCOPE_ONELEVEL, SCOPE_SUBTREE
from ldap import MOD_DELETE, MOD_REPLACE, MOD_ADD
from ldap import OPT_REFERRALS
from ldap import OPT_PROTOCOL_VERSION
from ldap import VERSION2, VERSION3
# Exceptions
from ldap import LDAPError
from ldap import INVALID_CREDENTIALS
from ldap import INAPPROPRIATE_AUTH
from ldap import UNWILLING_TO_PERFORM
from ldap import INVALID_DN_SYNTAX
from ldap import NO_SUCH_OBJECT
from ldap import SERVER_DOWN
#from ldap import SIZELIMIT_EXCEEDED

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.Image import Image

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter
from Products.CPSSchemas.Field import ValidationError

from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed
from Products.CPSDirectory.BaseDirectory import ConfigurationError
from Products.CPSDirectory.BaseDirectory import _replaceProperty


#
# UTF-8
#

default_encoding = sys.getdefaultencoding()
if default_encoding == 'ascii':
    default_encoding = 'latin1'

def toUTF8(s):
    if not isinstance(s, UnicodeType):
        s = unicode(s, default_encoding)
    return s.encode('utf-8')

#
# LDAP escaping
#

escape_ldap_values_chars = '\\;,+"<> \t\n\r'
escape_ldap_values = {}
for c in escape_ldap_values_chars:
    escape_ldap_values[c] = '\\'+hex(ord(c))[2:].upper()
del c

def stringToLDAP(s):
    """Convert a UTF-8 string to its LDAP escaped encoding."""
    return ''.join([escape_ldap_values.get(c, c) for c in s])

# These work on LDAP-formatted DNs encoded strings

def explodeDN(dn):
    """Explode a dn into list of rdns."""
    return ldap.explode_dn(dn)

def implodeDN(rdns):
    """Implode a sequence of rdns into a dn."""
    return ','.join(rdns)

def makeCanonicalDN(dn):
    return implodeDN(explodeDN(dn))

def isCanonicalDN(dn):
    return dn == makeCanonicalDN(dn)

def explodeRDN(rdn):
    """Explode a rdn into a list of avas.

    The rdn may be a full dn, in which case only the first rdn is used.

    An ava (attribute/value) is a string of the form foo=bar.
    A rdn may be multivalued, avas are separated by '+'.
    """
    return ldap.explode_rdn(rdn)

def implodeRDN(avas):
    """Implode a sequence of avas into a rdn."""
    return '+'.join(avas)


class LDAPBackingDirectory(BaseDirectory):
    """LDAP Backing Directory.

    A directory that connects to an LDAP server.

    This directory has two special fields, 'dn' and 'base_dn'.

    - 'dn' is read-only and is always used as the id.
      The dn is always in canonical LDAP form, that is, encoded in UTF-8
      and further escaped for LDAP consumption.
      Example: drink=caf\C3\A9,c=it

    - 'base_dn' is read-only.
    """

    meta_type = 'CPS LDAP Backing Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': "Field for password (if authentication)"},
        {'id': 'password_encryption', 'type': 'selection', 'mode': 'w',
         'label': "Password encryption",
         'select_variable': 'all_password_encryptions'},
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
    _properties = _replaceProperty(
        _properties, 'id_field',
        {'id': 'id_field', 'type': 'string', 'mode': '', # read-only
         'label': 'Field for entry id'})

    id_field = 'dn'
    title_field = 'cn'

    password_field = ''
    password_encryption = 'none'
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

    ldap_scope_c = SCOPE_SUBTREE
    ldap_search_classes_c = ['person']
    ldap_search_classes_filter = '(objectClass=person)'
    ldap_object_classes_c = ['top', 'person']

    all_password_encryptions = ('none',)
    all_ldap_scopes = ('ONELEVEL', 'SUBTREE')

    _v_conn = None

    def __init__(self, id, **kw):
        BaseDirectory.__init__(self, id, **kw)

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        BaseDirectory._postProcessProperties(self)
        # Make dns canonical
        self.ldap_base = makeCanonicalDN(self.ldap_base)
        # Convert string stuff
        conv = {'ONELEVEL': SCOPE_ONELEVEL,
                'SUBTREE': SCOPE_SUBTREE,
                }
        self.ldap_scope_c = conv.get(self.ldap_scope, SCOPE_ONELEVEL)
        # Split object classes for creation
        classes = self.ldap_object_classes
        classes = [x.strip() for x in classes.split(',')]
        classes = filter(None, classes)
        self.ldap_object_classes_c = classes
        self.ldap_object_classes = ', '.join(classes)
        # Split object classes for search
        classes = self.ldap_search_classes
        classes = [x.strip() for x in classes.split(',')]
        classes = filter(None, classes)
        self.ldap_search_classes_c = classes
        self.ldap_search_classes = ', '.join(classes)
        # Prebuild objectClass search filter
        if classes:
            filt = ''.join(['(objectClass=%s)' % c for c in classes])
            if len(classes) > 1:
                filt = '(|%s)' % filt
        else:
            filt = '(objectClass=*)'
        self.ldap_search_classes_filter = filt
        # Reset connection (XXX problems with multiple threads)
        self._v_conn = None

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        dir = self
        adapters = [LDAPBackingStorageAdapter(schema, id, dir, **kw)
                    for schema in self._getSchemas(search=search)]
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
        if title_field == 'dn':
            results = self.searchEntries()
            res = [(id, id) for id in results]
        else:
            results = self.searchEntries(return_fields=[title_field])
            res = [(id, entry[title_field]) for id, entry in results]
        return res

    security.declarePublic('searchEntries')
    def searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.

        LDAP specifics:
        - Returns all entries if query is empty.
        - Keys with empty values are removed.
        - Keys with value '*' search for an existing field.
        """
        schema = self._getSchemas()[0]
        all_field_ids = schema.keys()

        # Find attrs needed to compute returned fields.
        # XXX this code is also in ZODBDirectory and should be factored out
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

        filter = self._buildFilter(kw)
        res = self._searchEntries(filter, attrs)
        return res

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        if not isCanonicalDN(id):
            raise KeyError("Entry DN '%s' is not canonical")
        try:
            self.checkUnderBase(id)
        except ValueError:
            return 0
        return self.existsLDAP(id)

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.

        Asks the backing directories, all of them must be authenticating.
        """
        return not not self.password_field

    security.declarePrivate('getEntryAuthenticated')
    def getEntryAuthenticated(self, id, password, **kw):
        """Get and authenticate an entry.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """
        if not id.strip():
            # We don't want to cause an empty LDAP search.
            raise AuthenticationFailed
        return self._getEntryKW(id, password=password, **kw)

    security.declarePublic('createEntry')
    def createEntry(self, entry):
        """Create an entry in the directory."""
        self.checkCreateEntryAllowed(entry=entry)

        ldap_attrs = self.convertDataToLDAP(entry)
        if entry.get('dn'):
            dn = entry['dn']
            self.checkUnderBase(dn)
        else:
            # Synthesize a dn for creation
            rdn_attr = ldap_attrs.get(self.ldap_rdn_attr, [])
            if not rdn_attr:
                raise ValueError("Missing rdn attribute '%s' in entry" %
                                 self.ldap_rdn_attr)
            rdn = rdn_attr[0].strip() # If multivalued, take the first one.
            ava = '%s=%s' % (self.ldap_rdn_attr, rdn)
            if self.ldap_scope_c == SCOPE_ONELEVEL:
                base_dn = self.ldap_base
            else: # SCOPE_SUBTREE
                if not entry.has_key('base_dn'):
                    raise ValueError("Missing base_dn in entry")
                base_dn = entry['base_dn']
                if not isCanonicalDN(base_dn):
                    raise ValueError("base_dn '%s' is not canonical" % base_dn)
                if not (','+base_dn).endswith(','+self.ldap_base):
                    raise ValueError("base_dn '%s' must be under base '%s'" %
                                     (base_dn, self.ldap_base))
            dn = implodeDN((ava, base_dn))

        if self.hasEntry(dn):
            raise KeyError("Entry '%s' already exists" % dn)

        ldap_attrs['objectClass'] = list(self.ldap_object_classes_c)
        self.insertLDAP(dn, ldap_attrs)

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed(id=id)
        if not self.hasEntry(id):
            raise KeyError("No entry '%s'" % id)
        self.deleteLDAP(id)

    #
    # Internal
    #

    def _getAdapterForPartialData(self, attrs):
        """Get an adapter for partial data."""
        dir = self
        schema = self._getSchemas()[0] # XXX
        adapter = LDAPBackingStorageAdapter(schema, None, dir, field_ids=attrs)
        return adapter

    def _getEntryFromLDAP(self, id, field_ids, password=None):
        """Get LDAP entry for a user.

        Returns converted values.
        """
        filter = self.objectClassSearchFilter()
        try:
            results = self.searchLDAP(id, SCOPE_BASE, filter,
                                      field_ids, password=password)
        except (INVALID_CREDENTIALS, INAPPROPRIATE_AUTH,
                UNWILLING_TO_PERFORM):
            # INAPPROPRIATE_AUTH: tried auth on entry without userPassword
            # UNWILLING_TO_PERFORM: unauthenticated bind (DN with no password)
            # disallowed
            if password is None:
                LOG('_getEntryFromLDAP', ERROR,
                    "Invalid credentials for directory %s" % self.getId())
                raise INVALID_CREDENTIALS
            else:
                LOG('_getEntryFromLDAP', TRACE,
                    "Invalid credentials for %s" % id)
                raise AuthenticationFailed
        if not results:
            raise KeyError("No entry '%s'" % id)
        dn, ldap_entry = results[0]
        entry = self.convertDataFromLDAP(dn, ldap_entry)
        return entry

    def _buildFilter(self, query):
        """Build an LDAP filter from a query.

        Returns a non-encoded LDAP filter. It will have to be UTF-8
        encoded before being passed to LDAP.
        """
        all_field_ids = self._getSchemas()[0].keys()
        filter_elems = [self.objectClassSearchFilter()]
        for key, value in query.items():
            if not key in all_field_ids:
                continue
            if key == 'dn': # XXX treat it
                continue
            if key == 'base_dn': # XXX treat it too !
                continue
            if '_' in key:
                # Invalid attribute for LDAP (Bad search filter (87)).
                LOG('LDAPBackingDirectory._buildFilter', ERROR,
                    "Invalid LDAP attribute '%s', ignored" % key)
                continue
            if not value:
                continue
            if key in self.search_substring_fields:
                fmt = '(%s=*%s*)'
            else:
                fmt = '(%s=%s)'
            if isinstance(value, StringType):
                if value == '*':
                    f = filter_format('(%s=*)', (key,))
                else:
                    f = filter_format(fmt, (key, value))
            elif isinstance(value, IntType):
                f = filter_format(fmt, (key, str(value)))
            elif isinstance(value, ListType) or isinstance(value, TupleType):
                # Always use exact match if a sequence is passed
                fl = [filter_format('(%s=%s)', (key, v))
                      for v in value if v]
                f = ''.join(fl)
                if len(fl) > 1:
                    f = '(|%s)' % f
            else:
                raise ValueError("Bad value %s for '%s'" % (`value`, key))
            if f:
                filter_elems.append(f)
        filter = ''.join(filter_elems)
        if len(filter_elems) > 1:
            filter = '(&%s)' % filter
        return filter

    def _searchEntries(self, filter, return_attrs):
        """Search entries according to filter."""
        if return_attrs is None:
            attrs = ['dn']
        else:
            attrs = return_attrs

        results = self.searchLDAP(self.ldap_base, self.ldap_scope_c,
                                  filter, attrs)

        if return_attrs is None:
            return [dn for dn, e in results]
        else:
            adapter = self._getAdapterForPartialData(return_attrs)
            res = []
            for dn, ldap_entry in results:
                entry = self.convertDataFromLDAP(dn, ldap_entry)
                # We must compute a partial datamodel for each result,
                # to get correct computed fields.
                data = adapter._getData(entry=entry)
                res.append((dn, data))
            return res

    security.declarePrivate('objectClassSearchFilter')
    def objectClassSearchFilter(self):
        return self.ldap_search_classes_filter

    # XXX security
    def getImageFieldData(self, entry_id, field_id, REQUEST, RESPONSE):
        """Gets the raw data from a non ZODB image field"""
        entry = self.getEntry(entry_id)
        value = entry[field_id]
        if value is None:
            return ''
        else:
            return value.index_html(REQUEST, RESPONSE)

    #
    # LDAP code
    #

    security.declarePrivate('convertDataToLDAP')
    def convertDataToLDAP(self, data, ignored_attrs=(), keep_empty=0):
        """Convert a data mapping into a correct LDAP one.

        The values for an LDAP entry are always lists.
        Uses the schema to decide how conversion is done.

        Skips ignored_attrs. Keeps empty attributes if keep_empty.
        """
        ldap_attrs = {}
        for field_id, field in self._getSchemas()[0].items(): # XXX
            if field.write_ignore_storage:
                continue
            if field_id in ('dn', 'base_dn'):
                # Never modifiable directly.
                continue
            if field_id in ignored_attrs:
                continue
            if not data.has_key(field_id):
                continue
            value = data[field_id]
            if not value and not keep_empty:
                continue
            values = field.convertToLDAP(value)
            if not values:
                values = [''] # Means 'delete' for modify operations.
            ldap_attrs[field_id] = values
        return ldap_attrs

    security.declarePrivate('convertDataFromLDAP')
    def convertDataFromLDAP(self, dn, ldap_entry):
        """Convert LDAP values to a user data mapping."""
        entry = {}
        ldap_entry['dn'] = [dn]
        for field_id, field in self._getSchemas()[0].items(): # XXX
            if not ldap_entry.has_key(field_id):
                continue
            values = ldap_entry[field_id]
            try:
                value = field.convertFromLDAP(values)
            except ValidationError:
                # XXX
                raise
            entry[field_id] = value
        return entry

    security.declarePrivate('checkUnderBase')
    def checkUnderBase(self, dn):
        """Check that dn is under the base."""
        if not isCanonicalDN(dn):
            raise KeyError("DN '%s' is not canonical" % dn)
        if not (','+dn).endswith(','+self.ldap_base):
            raise ValueError("DN '%s' must be under base '%s'" %
                             (dn, self.ldap_base))

    security.declarePrivate('connectLDAP')
    def connectLDAP(self, bind_dn=None, bind_password=None):
        """Get or initialize a connection to the LDAP server.

        If bind_dn and bind_password are provided, bind using them.
        Otherwise bind using the global bind dn and password.
        """
        conn = self._v_conn
        if conn is None:
            if self.ldap_use_ssl:
                proto = 'ldaps'
            else:
                proto = 'ldap'
            conn_str = '%s://%s:%s/' % (proto, self.ldap_server, self.ldap_port)

            LOG('connectLDAP', TRACE, 'initialize conn_str=%s' % conn_str)
            conn = ldap.initialize(conn_str)
            try:
                conn.set_option(OPT_PROTOCOL_VERSION, VERSION3)
            except LDAPError:
                conn.set_option(OPT_PROTOCOL_VERSION, VERSION2)

            # Auto-chase referrals.
            try:
                conn.set_option(OPT_REFERRALS, 1)
            except LDAPError:
                # Forget about it.
                LOG('LDAPBackingDirectory.connect', DEBUG, 'No referrals')
                pass

            #conn.manage_dsa_it(0)

            conn._cps_bound_dn = None
            conn._cps_bound_password = None

            self._v_conn = conn

        # Check how to bind
        if bind_dn is None:
            bind_dn = self.ldap_bind_dn
            bind_password = self.ldap_bind_password

        if (conn._cps_bound_dn == bind_dn and
            conn._cps_bound_password == bind_password):
            return conn

        # Bind with authentication
        conn._cps_bound_dn = None
        conn._cps_bound_password = None
        LOG('connectLDAP', TRACE, "bind_s dn=%s" % bind_dn)
        try:
            conn.simple_bind_s(bind_dn, bind_password)
        except SERVER_DOWN:
            raise ConfigurationError("Directory '%s': LDAP server is down"
                                     % self.getId())
        # may raise INVALID_CREDENTIALS
        conn._cps_bound_dn = bind_dn
        conn._cps_bound_password = bind_password

        return conn

    security.declarePrivate('existsLDAP')
    def existsLDAP(self, dn):
        """Return true if the entry exists."""
        try:
            conn = self.connectLDAP()
            LOG('existsLDAP', TRACE, "search_s dn=%s" % dn)
            filter = self.objectClassSearchFilter()
            res = conn.search_s(dn, SCOPE_BASE, filter, ['dn'])
            LOG('existsLDAP', TRACE, " -> results=%s" % (res,))
        except NO_SUCH_OBJECT:
            return 0
        return len(res) != 0

    security.declarePrivate('searchLDAP')
    def searchLDAP(self, base, scope, filter, attrs, password=None):
        """Search in LDAP.

        Returns a sequence of (dn, entry).
        entry's values are already converted from LDAP format.

        If password is provided, attempt to bind using it.
        """
        if password is None:
            conn = self.connectLDAP()
        else:
            if scope != SCOPE_BASE:
                raise ValueError("Incorrect scope for authenticated search")
            try:
                if ',' not in base:
                    # Avoid doing an LDAP request if we know we'll fail.
                    raise INVALID_DN_SYNTAX
                conn = self.connectLDAP(base, toUTF8(password))
            except INVALID_DN_SYNTAX:
                LOG('searchLDAP', TRACE, "Invalid credentials (dn syntax) for %s" % base)
                return []

        LOG('searchLDAP', TRACE, "search_s base=%s scope=%s filter=%s attrs=%s" %
            (base, scope, filter, attrs))
        try:
            ldap_entries = conn.search_s(base, scope, toUTF8(filter), attrs)
        except NO_SUCH_OBJECT:
            raise ConfigurationError("Directory '%s': Invalid search base "
                                     "'%s'" % (self.getId(), base))
        except SERVER_DOWN:
            raise ConfigurationError("Directory '%s': LDAP server is down"
                                     % self.getId())
        LOG('searchLDAP', TRACE, " -> results=%s" % (ldap_entries[:20],))
        #except NO_SUCH_OBJECT:
        #except SIZELIMIT_EXCEEDED:
        return ldap_entries

    security.declarePrivate('deleteLDAP')
    def deleteLDAP(self, dn):
        """Delete an entry from LDAP."""
        # maybe check read_only
        conn = self.connectLDAP()
        LOG('deleteLDAP', TRACE, "delete_s dn=%s" % dn)
        conn.delete_s(dn)

    security.declarePrivate('insertLDAP')
    def insertLDAP(self, dn, ldap_attrs):
        """Insert a new entry in LDAP."""
        # maybe check read_only
        attrs_list = [(k, v) for k, v in ldap_attrs.items()]
        conn = self.connectLDAP()
        LOG('insertLDAP', TRACE, "add_s dn=%s attrs=%s" % (dn, attrs_list))
        conn.add_s(dn, attrs_list)

    security.declarePrivate('modifyLDAP')
    def modifyLDAP(self, dn, ldap_attrs):
        """Modify an entry in LDAP."""
        # maybe check read_only
        conn = self.connectLDAP()

        rdn = explodeDN(dn)[0]
        rdn_split = explodeRDN(rdn)
        rdn_attrs = [ava.split('=')[0] for ava in rdn_split]

        # Get current entry
        LOG('modifyLDAP', TRACE, "search_s base dn=%s" % dn)
        # (use objectClass=* because dn is already assumed valid
        #  and also we'd like the *LDAP methods to be generic)
        res = conn.search_s(dn, SCOPE_BASE, '(objectClass=*)')
        LOG('modifyLDAP', TRACE, " -> results=%s" % (res,))
        if not res:
            raise KeyError("No entry '%s'" % dn)
        cur_dn, cur_ldap_entry = res[0]

        # Find modifications
        mod_list = []
        for key, values in ldap_attrs.items():
            if key == 'dn':
                # No way to changed dn like that
                # Do it through modrdn XXX
                continue
            if cur_ldap_entry.has_key(key):
                if values == ['']:
                    if key in rdn_attrs:
                        raise ValueError("Cannot delete rdn attribute '%s'"
                                         % key)
                    mod_list.append((MOD_DELETE, key, None))
                elif cur_ldap_entry[key] != values:
                    if key in rdn_attrs:
                        raise ValueError("Modrdn not implemented")
                    mod_list.append((MOD_REPLACE, key, values))
            else:
                if values != ['']:
                    mod_list.append((MOD_ADD, key, values))
        if not mod_list:
            return

        LOG('modifyLDAP', TRACE, "modify_s dn=%s mod_list=%s" % (dn, mod_list))
        conn.modify_s(dn, mod_list)


InitializeClass(LDAPBackingDirectory)


class LDAPBackingStorageAdapter(BaseStorageAdapter):
    """LDAP Backing Storage Adapter

    This adapter gets and sets data from an LDAP server.
    """

    def __init__(self, schema, id, dir, password=None, **kw):
        """Create an Adapter for a schema."""
        self._id = id
        self._dir = dir
        self._password = password
        BaseStorageAdapter.__init__(self, schema, **kw)

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        if id is None:
            # Creation.
            return self.getDefaultData()

        field_ids = self.getFieldIds()
        entry = self._dir._getEntryFromLDAP(id, field_ids,
                                            password=self._password)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        if field_id == 'dn':
            return entry['dn']
        if field_id == 'base_dn':
            dn = entry['dn']
            return implodeDN(explodeDN(dn)[1:])
        if not entry.has_key(field_id):
            return field.getDefault()
        return entry[field_id]

    def _setData(self, data):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data)
        dn = self._id

        # Find the rdn attr.
        rdn = dn.split(',')[0]
        rdn_attr, rdn_value = rdn.split('=', 1)

        # XXX treat change of rdn

        dir = self._dir
        ldap_attrs = dir.convertDataToLDAP(data, keep_empty=1)
        dir.modifyLDAP(dn, ldap_attrs)

    def _getContentUrl(self, entry_id, field_id):
        return '%s/getImageFieldData?entry_id=%s&field_id=%s' % (
            self._dir.absolute_url(), entry_id, field_id)


InitializeClass(LDAPBackingStorageAdapter)
