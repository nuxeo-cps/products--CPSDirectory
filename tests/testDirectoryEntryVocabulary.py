import unittest
from Products.CPSDirectory.DirectoryEntryVocabulary import DirectoryEntryVocabulary

class FakeDir:
    def getEntry(self, id, default=None):
        return None

class TestDirectoryEntryVocabulary(unittest.TestCase):

    def _getDirectory(self):
        return FakeDir()

    def test_keys(self):
        entry_voc = DirectoryEntryVocabulary('ok')
        entry_voc._getDirectory = self._getDirectory
        self.assertEquals(entry_voc.keys(), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryEntryVocabulary))
    return suite
