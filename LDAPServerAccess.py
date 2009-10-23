# (C) Copyright 2008 Georges Racinet
# Author: Georges Racinet <georges@racinet.fr>
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
# $Id: LDAPBackingDirectory.py 52825 2008-04-23 15:56:27Z madarche $
"""LDAPServerAccess class.
"""

from logging import getLogger

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import SimpleItemWithProperties
from Products.CPSUtil.PropertiesPostProcessor import PropertiesPostProcessor
from Products.CPSDirectory.interfaces import ILDAPServerAccess

from zope.interface import implements

logger = getLogger('CPSDirectory.LDAPServerAccess')

class LDAPServerAccess(PropertiesPostProcessor, SimpleItemWithProperties):
    """LDAP Server Access.

    Instances of this class object store all needed information to perform
    a bind against a LDAP server.
    LDAPBackingDirectory instances refer to instances of this class to share
    bind info.
    """

    implements(ILDAPServerAccess)

    meta_type = 'LDAP Server Access'

    manage_options = (
        {'label': 'Export',
         'action': 'manage_genericSetupExport.html',
         },
        )

    security = ClassSecurityInfo()

    _propertiesBaseClass = SimpleItemWithProperties
    _properties = (
        {'id': 'server', 'type': 'string', 'mode': 'w',
         'label': 'LDAP server'},
        {'id': 'port', 'type': 'int', 'mode': 'w',
         'label': 'LDAP port'},
        {'id': 'use_ssl', 'type': 'boolean', 'mode': 'w',
         'label': 'LDAP use ssl'},
        {'id': 'bind_dn', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind dn'},
        {'id': 'bind_password', 'type': 'string', 'mode': 'w',
         'label': 'LDAP bind password'},
        )

    # same defaults as customary in CPSLDAPSetup
    server = 'localhost'
    port = 389
    use_ssl = 0
    bind_dn = 'cn=cps,ou=applications,dc=mysite,dc=net'
    bind_password = 'changeme'
    url = None

    def __init__(self, id, **kw):
        self.id = id
        self.manage_changeProperties(**kw)

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        old_url = self.url or '' # avoid None

        # updating default ports if needed. Side effect: user will have to
        # rechange the port if really wants to do ldaps on port 389
        if old_url.startswith('ldap://') and self.port == 389 and self.use_ssl:
            self.port = 636
        elif old_url.startswith('ldaps://') and self.port == 636 and not self.use_ssl:
            self.port = 389
            
        self._computeLdapUrl()

    def _computeLdapUrl(self):
        """Compute ldap url from properties."""
        
        proto = self.use_ssl and 'ldaps' or 'ldap'
        self.url = '%s://%s:%s/' % (proto, 
                                         self.server, self.port)


    #
    # API
    #

    security.declarePrivate('getLdapUrl')
    def getLdapUrl(self):
        """Return full ldap url for bind."""
        if self.url is None:
            self._computeLdapUrl()
        return self.url

    security.declarePrivate('getBindParameters')
    def getBindParameters(self):
        return self.bind_dn, self.bind_password

InitializeClass(LDAPServerAccess)
