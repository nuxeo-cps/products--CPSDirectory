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

import unittest

from Products.CPSDirectory.LDAPServerAccess import LDAPServerAccess

class TestLDAPServerAccess(unittest.TestCase):

    def setUp(self):
        self.access = LDAPServerAccess('access')

    def test_getLdapUrl(self):
        self.assertEquals(self.access.getLdapUrl(), 'ldap://localhost:389/')

        self.access.manage_changeProperties(server='example.com')
        self.assertEquals(self.access.getLdapUrl(), 'ldap://example.com:389/')

        # automatic switch of default port
        self.access.manage_changeProperties(use_ssl=True)
        self.assertEquals(self.access.getLdapUrl(), 'ldaps://example.com:636/')

        self.access.manage_changeProperties(use_ssl=False)
        self.assertEquals(self.access.getLdapUrl(), 'ldap://example.com:389/')
    
        self.access.manage_changeProperties(port=1389)
        self.assertEquals(self.access.getLdapUrl(), 'ldap://example.com:1389/')
    
        # not the default port: no change of port if ssl
        self.access.manage_changeProperties(use_ssl=True)
        self.assertEquals(self.access.getLdapUrl(), 'ldaps://example.com:1389/')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLDAPServerAccess))
    return suite
