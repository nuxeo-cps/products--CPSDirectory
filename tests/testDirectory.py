# TODO: 
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase


class TestDirectoryWithDefaultUserFolder(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('root')
        self.ws = self.portal.workspaces
        self.pd = self.portal.portal_directories

    def beforeTearDown(self):
        self.logout()

    def testDirectories(self):
        self.assertEquals(self.pd.groups.meta_type, "CPS Groups Directory")
        self.assertEquals(self.pd.members.meta_type, "CPS Members Directory")
        self.assertEquals(self.pd.roles.meta_type, "CPS Roles Directory")

    def testBasicSecurity(self):
        directories = (self.pd.members, self.pd.groups, self.pd.roles)

        for directory in directories:
            self.assert_(directory.isVisible())
            self.assert_(directory.isCreateEntryAllowed())

        self.logout()

        for directory in directories:
            self.assert_(not directory.isVisible())
            self.assert_(not directory.isCreateEntryAllowed())


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
            self.assert_(members.getEntry(member))

    def testMemberCreation(self):
        members = self.pd.members
        member_id = 'new_member'

        self.assert_(not members.hasEntry(member_id))
        search_result = members.searchEntries(member=member_id)
        self.assert_(not search_result)
        self.assert_(not member_id in members.listEntryIds())
        self.assertRaises(KeyError, members.getEntry, member_id)

        members.createEntry({'id': member_id})

        self.assert_(members.hasEntry(member_id))
        search_result = members.searchEntries(id=member_id)
        self.assertEquals(search_result, [member_id])
        self.assert_(member_id in members.listEntryIds())

        entry = members.getEntry(member_id)
        self.assertEquals(entry, {'password': '__NO_PASSWORD__', 
            'id': member_id, 'roles': [], 'givenName': '', 'groups': (), 
            'sn': '', 'email': '', 'fullname': ' ', 'confirm': ''})

        # XXX: this shouldn't succeed
        #self.assertRaises(ValueError, members.createEntry, 
        #    {'id': member_id})

        # XXX: not implemented yet
        #members.deleteEntry(member_id)
        #self.assert_(not members.hasEntry(member_id))

    #
    # Groups
    #
    def testDefaultGroups(self):
        groups = self.pd.groups

        # XXX: it is a tuple, but later it is a list. I consider this
        # an error.
        default_groups = ()

        self.assertEquals(groups.listEntryIds(), default_groups)
        search_result = groups.searchEntries()
        # XXX: see above remark
        self.assertEquals(search_result, list(default_groups))

    def testGroupCreation(self):
        groups = self.pd.groups
        group_id = 'new_group'

        self.assert_(not groups.hasEntry(group_id))
        search_result = groups.searchEntries(group=group_id)
        self.assert_(not search_result)
        self.assert_(not group_id in groups.listEntryIds())

        groups.createEntry({'group': group_id})

        self.assert_(groups.hasEntry(group_id))
        search_result = groups.searchEntries(id=group_id)
        self.assertEquals(search_result, [group_id])
        self.assert_(group_id in groups.listEntryIds())

        self.assertRaises(ValueError, groups.createEntry, 
            {'group': group_id})

        # XXX: not implemented yet
        #groups.deleteEntry(group_id)
        #self.assert_(not groups.hasEntry(group_id))

    def testMemberQueryingOnGroups(self):
        groups = self.pd.groups
        group_id = 'new_group2'
        groups.createEntry({'group': group_id})

        members = self.pd.members
        member_id = 'new_member2'
        members.createEntry({'id': member_id, 'groups': [group_id,]})

        search_result = members.searchEntries(groups=[group_id])
        #print "testMemberQueryingOnGroups search_result = %s" % str(search_result)
        self.assertEquals(search_result, [member_id])

    #
    # Roles
    #
    def testDefaultRoles(self):
        # XXX this test assumes too much about existing roles.
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

        # XXX: not implemented yet
        #roles.deleteEntry(role_id)
        #self.assert_(not roles.hasEntry(role_id))

    #
    # TODO: add a more complex scenario here
    #


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryWithDefaultUserFolder))
    return suite

