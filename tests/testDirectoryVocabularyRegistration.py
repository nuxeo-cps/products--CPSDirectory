"""Integration tests on vocabulary registration
"""
from Testing import ZopeTestCase
import unittest

# Installing CPSDirectory to trigger registrations
product_name = __name__.split('.')[0]
ZopeTestCase.installProduct(product_name)

class TestDirectoryVocabularyRegistration(unittest.TestCase):

    def testIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Vocabulary' in VTR.listTypes())
        self.assertEquals(VTR.getType('CPS Directory Vocabulary').meta_type,
            'CPS Directory Vocabulary')

    def testDirectoryEntryVocabulatryIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Entry Vocabulary' in VTR.listTypes())
        meta_type = VTR.getType('CPS Directory Entry Vocabulary').meta_type
        self.assertEquals(meta_type, 'CPS Directory Entry Vocabulary')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryVocabularyRegistration))
    return suite
