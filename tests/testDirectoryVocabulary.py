# TODO: 
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase


class TestDirectoryVocabulary(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('root')
        self.ws = self.portal.workspaces
        self.pd = self.portal.portal_directories
        self.pv = self.portal.portal_vocabularies

    def beforeTearDown(self):
        self.logout()

    def testIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Vocabulary' in VTR.listTypes())
        self.assertEquals(VTR.getType('CPS Directory Vocabulary').meta_type, 
            'CPS Directory Vocabulary')

    def testMembers(self):
        members = self.pv.members
        self.assertEquals(members._getDirectory(), self.pd.members)
        self.assertEquals(members.keys(), ['root', 'test_user_1_'])
        root = members['root']
        self.assertEquals(members.get('root'), root)
        self.assertEquals(members.get('toto'), None)
        self.assertEquals(members.get('toto', 'titi'), 'titi')
        self.assert_(members.has_key('root'))
        members_ids = [ x[0] for x in members.items() ]
        self.assert_('root' in members_ids)
        members_values = [ x[1] for x in members.items() ]
        self.assert_(root in members_values)
        self.assert_(root in members.values())


    def testGroups(self):
        groups = self.pv.groups
        self.assertEquals(groups._getDirectory(), self.pd.groups)
        self.assertEquals(groups.keys(), ())

    def testRoles(self):
        roles = self.pv.roles
        self.assertEquals(roles._getDirectory(), self.pd.roles)
        for role in ['Manager', 'Member', 'Reviewer', 'SectionManager',
          'SectionReader', 'SectionReviewer', 'WorkspaceManager',
          'WorkspaceMember', 'WorkspaceReader']:
            keys = roles.keys()
            self.assert_(role in roles.keys())
            self.assert_(roles.has_key(role))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryVocabulary))
    return suite

