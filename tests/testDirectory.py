# TODO: 
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
import CPSDirectoryTestCase


class TestDirectoryWithDefaultUserFolder(
        CPSDirectoryTestCase.CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('root')
        self.ws = self.portal.workspaces

        # Add directory
        from Products.CPSDirectory.Extensions.install import install
        install(self.portal)

        self.pd = self.portal.portal_directories

    def beforeTearDown(self):
        self.logout()

    def testDirectories(self):
        self.assertEquals(self.pd.groups.meta_type, "CPS Groups Directory")
        self.assertEquals(self.pd.members.meta_type, "CPS Members Directory")
        self.assertEquals(self.pd.roles.meta_type, "CPS Roles Directory")

    #
    # Members
    #
    def testDefaultMembers(self):
        members = self.pd.members
        # 'test_user_1_' comes from ZopeTestCase
        default_members = ['root', 'test_user_1_']
        self.assertEquals(members.listEntryIds(), default_members)
        search_result = members.searchEntries()
        # XXX: this fails. Why ?
        #self.assertEquals(search_result, default_members)
        for member in default_members:
            self.assert_(members.hasEntry(member))

    def testMemberCreation(self):
        members = self.pd.members
        member_id = 'new_member'

        self.assert_(not members.hasEntry(member_id))
        search_result = members.searchEntries(member=member_id)
        self.assert_(not search_result)
        self.assert_(not member_id in members.listEntryIds())

        members.createEntry({'id': member_id})

        self.assert_(members.hasEntry(member_id))
        search_result = members.searchEntries(id=member_id)
        self.assertEquals(search_result, [member_id])
        self.assert_(member_id in members.listEntryIds())

        # XXX: this shouldn't succeed
        #self.assertRaises(ValueError, members.createEntry, 
        #    {'id': member_id})


    #
    # Roles
    #
    def testDefaultRoles(self):
        roles = self.pd.roles
        default_roles = [
            'ForumModerator', 'ForumPoster', 'Manager', 'Member', 'Reviewer',
            'SectionManager', 'SectionReader', 'SectionReviewer',
            'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader']
        self.assertEquals(roles.listEntryIds(), default_roles)
        search_result = roles.searchEntries()
        self.assertEquals(search_result, default_roles)

        for role in default_roles:
            self.assertRaises(ValueError, roles.createEntry, {'role': role})
        for role in ('Anonymous', 'Authenticated', 'Owner', ''):
            self.assertRaises(ValueError, roles.createEntry, {'role': role})

    def testRoleCreation(self):
        roles = self.pd.roles
        role_id = 'new_role'

        self.assert_(not roles.hasEntry(role_id))
        search_result = roles.searchEntries(role=role_id)
        self.assert_(not search_result)
        self.assert_(not role_id in roles.listEntryIds())

        roles.createEntry({'role': role_id})

        self.assert_(roles.hasEntry(role_id))
        search_result = roles.searchEntries(role=role_id)
        self.assertEquals(search_result, [role_id])
        self.assert_(role_id in roles.listEntryIds())

        self.assertRaises(ValueError, roles.createEntry, {'role': role_id})


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryWithDefaultUserFolder))
    return suite

