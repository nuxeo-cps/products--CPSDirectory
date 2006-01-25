# TODO:
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase
from AccessControl import Unauthorized

class TestDirectoryWithDefaultUserFolder(CPSDirectoryTestCase):

    def testDirectories(self):
        self.assertEquals(self.pd.groups.meta_type, "CPS ZODB Directory")
        self.assertEquals(self.pd.members.meta_type, "CPS ZODB Directory")
        self.assertEquals(self.pd.roles.meta_type, "CPS ZODB Directory")

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

        default_members = ['manager']
        self.assertEquals(members.listEntryIds(), default_members)
        # Only manager has a title set
        ids_and_titles = [('manager', 'Manager CPS')]
        self.assertEquals(members.listEntryIdsAndTitles(), ids_and_titles)

        # give an argument to search, otherwise no search is performed
        # FIXME, search using * is broken
        #search_result = members.searchEntries(**{members.id_field: '*'})
        #self.assertEquals(search_result, default_members)

        for member in default_members:
            self.assert_(members.hasEntry(member))
            self.assert_(members.getEntry(member))

    def testMemberCreation(self):
        members = self.pd.members
        member_id = 'new_member'

        self.assert_(not members.hasEntry(member_id))
        search_result = members.searchEntries(id=member_id)
        self.assertEquals(search_result, [])
        self.assertEquals(member_id in members.listEntryIds(), False)
        self.assertRaises(KeyError, members.getEntry, member_id)

        members.createEntry({'id': member_id})

        self.assert_(members.hasEntry(member_id))
        search_result = members.searchEntries(id=member_id)
        self.assertEquals(search_result, [member_id])
        self.assert_(member_id in members.listEntryIds())

        entry = members.getEntry(member_id)
        entry_desc = {
            'id': member_id,
            'fullname': member_id,
            'givenName': '',
            'sn': '',
            'email': '',
            'password': '',
            'confirm': '',
            'groups': [],
            'roles': [],
            'homeless': 0,
            }
        self.assertEquals(entry, entry_desc)

        self.assertRaises(KeyError, members.createEntry, {'id': member_id})

    def testMemberSearch(self):
        members = self.pd.members
        member_id1 = 'new_member5'
        member_email1 = 'exAMple@mail'
        member_sn1 = 'MemberFive'
        members.createEntry({'id': member_id1,
                             'email': member_email1,
                             'sn': member_sn1,
                             })
        member_id2 = 'new_member6'
        member_email2 = 'nospam@example.com'
        member_sn2 = 'six'
        members.createEntry({'id': member_id2,
                             'email': member_email2,
                             'sn': member_sn2,
                             })
        member_ids = [member_id1, member_id2]

        ### Without substrings, cache is cleared when changing config
        members.manage_changeProperties(search_substring_fields=[])

        # Basic searches
        res = members.searchEntries(id=member_id1)
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(id=[member_id1])
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(email=member_email1)
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(email=[member_email1])
        self.assertEquals(res, [member_id1])

        # Multi-field searches
        res = members.searchEntries(id=member_id1, email=[member_email1])
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(id=member_id1, email=[member_email2])
        self.assertEquals(res, [])

        # Failing substring searches
        res = members.searchEntries(id='new_mem')
        self.assertEquals(res, [])
        res = members.searchEntries(email='exam')
        self.assertEquals(res, [])
        res = members.searchEntries(email='example@mail') # different case
        self.assertEquals(res, [])

        ### With substrings, cache is cleared when changing config
        members.manage_changeProperties(
            search_substring_fields=['id', 'email'])

        # Basic searches
        res = members.searchEntries(id=member_id1)
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(id=[member_id1])
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(email=member_email1)
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(email=[member_email1])
        self.assertEquals(res, [member_id1])

        # Multi-field searches
        res = members.searchEntries(id=member_id1, email=[member_email1])
        self.assertEquals(res, [member_id1])
        res = members.searchEntries(id=member_id1, email=[member_email2])
        self.assertEquals(res, [])

        # Substring searches
        res = members.searchEntries(id='new_mem')
        self.assertEquals(res, member_ids)
        res = members.searchEntries(email='EXAM')
        self.assertEquals(res, member_ids)
        res = members.searchEntries(email='spam')
        self.assertEquals(res, [member_id2])
        res = members.searchEntries(email='aM')
        self.assertEquals(res, member_ids)
        res = members.searchEntries(email=['@']) # list implies exact match
        self.assertEquals(res, [])

    def testSetMemberPassword(self):
        members = self.pd.members
        member_id = 'new_member'
        members.createEntry({'id': member_id})
        members.editEntry({'id': member_id, members.password_field: 'password'})
        u = self.portal.acl_users.getUser(member_id)
        self.assert_(u._getPassword() == 'password')

    #
    # Groups
    #
    def testDefaultGroups(self):
        groups = self.pd.groups
        self.assertEquals(groups.listEntryIds(), [])
        search_result = groups.searchEntries()
        self.assertEquals(search_result, [])

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

        self.assertRaises(KeyError, groups.createEntry, {'group': group_id})

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
        self.assertEquals(search_result, [member_id])

    def testGroupSearch(self):
        groups = self.pd.groups
        group_id = 'new_group3'
        groups.createEntry({'group': group_id})

        members = self.pd.members
        member_id1 = 'new_member7'
        members.createEntry({'id': member_id1, 'groups': [group_id,]})
        member_id2 = 'new_member8'
        members.createEntry({'id': member_id2, 'groups': [group_id,]})
        member_ids = [member_id1, member_id2]

        ### Without substrings, cache is cleared when changing config
        groups.manage_changeProperties(search_substring_fields=[])

        # Basic searches
        res = groups.searchEntries(members=member_ids)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(members=[member_id1])
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(members=member_id1)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group=group_id)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group=[group_id])
        self.assertEquals(res, [group_id])

        # Multi-field searches
        res = groups.searchEntries(members=member_id1, group=group_id)
        self.assertEquals(res, [group_id])

        # Failing substring searches
        res = groups.searchEntries(members='new_mem')
        self.assertEquals(res, [])
        res = groups.searchEntries(group='new_gro')
        self.assertEquals(res, [])


        ### With substrings, cache is cleared when changing config
        groups.manage_changeProperties(
            search_substring_fields=['group', 'members'])

        # Basic searches
        res = groups.searchEntries(members=member_ids)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(members=[member_id1])
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(members=member_id1)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group=group_id)
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group=[group_id])
        self.assertEquals(res, [group_id])

        # Multi-field searches
        res = groups.searchEntries(members=member_id1, group=group_id)
        self.assertEquals(res, [group_id])

        # Substring searches
        res = groups.searchEntries(members='new_mem')
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group='new_group')
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group='new_gro')
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group='ew_gro')
        self.assertEquals(res, [group_id])
        res = groups.searchEntries(group=['new_gro']) # list: exact match
        self.assertEquals(res, [])

    #
    # Roles
    #
    # FIXME: this test is desactivated because new roles can be added by
    # other products
    def _testDefaultRoles(self):
        # XXX this test assumes too much about existing roles.
        roles = self.pd.roles

        okroles1 = ['Manager', 'Member', 'Reviewer',
                    'SectionManager', 'SectionReader', 'SectionReviewer',
                    'WorkspaceManager', 'WorkspaceMember', 'WorkspaceReader']
        okroles2 = okroles1[:] + ['ForumModerator', 'ForumPoster']
        okroles1.sort()
        okroles2.sort()

        res = roles.listEntryIds()
        res.sort()
        if res == okroles2:
            okroles = okroles2
        else:
            okroles = okroles1
        self.assertEquals(res, okroles)

        res = roles.searchEntries()
        res.sort()
        self.assertEquals(res, okroles)

        for role in okroles:
            self.assertRaises(KeyError, roles.createEntry, {'role': role})
        for role in ('Anonymous', 'Authenticated', 'Owner', ''):
            self.assertRaises(KeyError, roles.createEntry, {'role': role})

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

        self.assertRaises(KeyError, roles.createEntry, {'role': role_id})

        # XXX: not implemented yet
        #roles.deleteEntry(role_id)
        #self.assert_(not roles.hasEntry(role_id))

    def testRoleSearch(self):
        roles = self.pd.roles
        role_id = 'new_role3'
        roles.createEntry({'role': role_id})

        members = self.pd.members
        member_id1 = 'new_member3'
        members.createEntry({'id': member_id1, 'roles': [role_id,]})
        member_id2 = 'new_member4'
        members.createEntry({'id': member_id2, 'roles': [role_id,]})
        member_ids = [member_id1, member_id2]

        ### Without substrings, cache is cleared when changing config
        roles.manage_changeProperties(search_substring_fields=[])

        # Basic searches
        res = roles.searchEntries(members=member_ids)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(members=[member_id1])
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(members=member_id1)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role=role_id)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role=[role_id])
        self.assertEquals(res, [role_id])

        # Multi-field searches
        res = roles.searchEntries(members=member_id1, role=role_id)
        self.assertEquals(res, [role_id])

        # Failing substring searches
        res = roles.searchEntries(members='new_mem')
        self.assertEquals(res, [])
        res = roles.searchEntries(role='new_rol')
        self.assertEquals(res, [])

        ### With substrings, cache is cleared when changing config
        roles.manage_changeProperties(
            search_substring_fields=['role', 'members'])

        # Basic searches
        res = roles.searchEntries(members=member_ids)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(members=[member_id1])
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(members=member_id1)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role=role_id)
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role=[role_id])
        self.assertEquals(res, [role_id])

        # Multi-field searches
        res = roles.searchEntries(members=member_id1, role=role_id)
        self.assertEquals(res, [role_id])

        # Substring searches
        res = roles.searchEntries(members='new_mem')
        self.assertEquals(res, [role_id]) # never substring on members
        res = roles.searchEntries(role='new_rol')
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role='ew_rol')
        self.assertEquals(res, [role_id])
        res = roles.searchEntries(role=['new_rol']) # list implies exact match
        self.assertEquals(res, [])


    #
    # TODO: add a more complex scenario here
    #


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryWithDefaultUserFolder))
    return suite

