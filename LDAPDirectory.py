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

from zLOG import LOG, DEBUG, PROBLEM, ERROR

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
except ImportError:
    from Products.LDAPUserFolder.LDAPDelegate import \
         LDAPDelegate, ldap

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
        LOG('listEntryIds', DEBUG, 'servers %s' % `self._delegate._servers`)
        id_attr = self.id_field
        res = self._delegate.search(base=self.ldap_base,
                                    scope=self.ldap_scope,
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

    security.declarePublic('searchEntries')
    def searchEntries(self, **kw):
        """Search for entries in the directory.
        """
        raise NotImplementedError

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

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        dir = self._dir

        # XXX treat case where id_field == 'dn' (use base=dn)
        # XXX use self.ldap_object_classes here too
        filter = '(&(%s=%s)(objectClass=*))' % (dir.id_field, id)
        field_ids = self._schema.keys()

        res = dir._delegate.search(base=dir.ldap_base, scope=dir.ldap_scope,
                                   filter=filter,
                                   attrs=field_ids,
                                   bind_dn=dir.ldap_bind_dn,
                                   bind_pwd=dir.ldap_bind_password)

        if res['exception']:
            LOG('LDAPDirectory', ERROR, 'Error talking to server: %s'
                % res['exception'])
            raise ValueError(res['exception']) # XXX do better ?

        if not res['size']:
            raise ValueError("No user '%s'" % id)

        result = res['results'][0]
        data = {}
        for field_id in field_ids:
            if field_id == 'dn':
                value = result['dn']
            else:
                value = result[field_id][0] # XXX treat multi-valued args!!!
            data[field_id] = value
        return data

    def setData(self, data):
        """Set data to the entry, from a mapping."""
        raise NotImplementedError

InitializeClass(LDAPStorageAdapter)
