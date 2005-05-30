# TODO:
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase
from Products.CPSDirectory.DirectoryEntryVocabulary import DirectoryEntryVocabulary

class FakeDir:
    def getEntry(self, id, default=None):
        return None

class TestDirectoryEntryVocabulary(CPSDirectoryTestCase):

    def _getDirectory(self):
        return FakeDir()

    def testIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Entry Vocabulary' in VTR.listTypes())
        self.assertEquals(VTR.getType('CPS Directory Entry Vocabulary').meta_type,
            'CPS Directory Entry Vocabulary')

    def test_keys(self):
        entry_voc = DirectoryEntryVocabulary('ok')
        entry_voc._getDirectory = self._getDirectory
        self.assertEquals(entry_voc.keys(), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryEntryVocabulary))
    return suite
