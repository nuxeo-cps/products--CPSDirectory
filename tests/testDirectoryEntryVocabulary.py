# TODO:
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase

class TestDirectoryEntryVocabulary(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('manager')
        self.ws = self.portal.workspaces
        self.pd = self.portal.portal_directories
        self.pv = self.portal.portal_vocabularies

    def beforeTearDown(self):
        self.logout()

    def testIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Entry Vocabulary' in VTR.listTypes())
        self.assertEquals(VTR.getType('CPS Directory Entry Vocabulary').meta_type,
            'CPS Directory Entry Vocabulary')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryEntryVocabulary))
    return suite
