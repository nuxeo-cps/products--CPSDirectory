# TODO: 
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from pprint import pprint
import unittest
from Testing import ZopeTestCase
import CPSDirectoryTestCase


class TestDirectory(CPSDirectoryTestCase.CPSDirectoryTestCase):
    def afterSetUp(self):
        self.login('root')
        self.ws = self.portal.workspaces

        # Add directory
        from Products.CPSDirectory.Extensions.install import install
        install(self.portal)

        self.pd = self.portal.portal_directories

    def beforeTearDown(self):
        self.logout()

    def test(self):
        self.assertEquals(self.pd.groups.meta_type, "CPS Groups Directory")
        self.assertEquals(self.pd.members.meta_type, "CPS Members Directory")
        self.assertEquals(self.pd.roles.meta_type, "CPS Roles Directory")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectory))
    return suite

