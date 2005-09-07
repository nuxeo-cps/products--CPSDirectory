import os, sys

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import Unauthorized
from OFS.Folder import Folder

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot

from Products.CPSDirectory.DirectoryTool import DirectoryTool

class TestDirectoryTool(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = DirectoryTool()
        self.portal = self.root.portal
        self.pd = self.portal.portal_directories

    def makeSchema(self):
        stool = self.portal.portal_schemas
        s_members = FakeSchema({
            'id': FakeField(),
            'cn': FakeField(),
            'groups': FakeField(),
            })
        stool._setObject('members', s_members)

    def makeDir(self):
        from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
        dtool = self.portal.portal_directories
        dir = ZODBDirectory('members',
                           id_field='id',
                           title_field='cn',
                           schema='members',
                           acl_directory_view_roles='test_role_1_',
                           acl_entry_create_roles='test_role_1_',
                           acl_entry_delete_roles='test_role_1_',
                           acl_entry_view_roles='test_role_1_',
                           acl_entry_edit_roles='test_role_1_',
                           )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.members
        invisible = ZODBDirectory('invisible',
                           id_field='id',
                           title_field='cn',
                           schema='members',
                           acl_directory_view_roles='',
                           acl_entry_create_roles='test_role_1_',
                           acl_entry_delete_roles='test_role_1_',
                           acl_entry_view_roles='test_role_1_',
                           acl_entry_edit_roles='test_role_1_',
                           )
        dtool._setObject(invisible.getId(), invisible)

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

    def test_listVisibleDirectories(self):
        dir_list = self.pd.listVisibleDirectories()
        self.assertEquals(dir_list, ['members'])

    def test_crossGetList(self):
        dir, pd = self.dir, self.pd
        dir_id = dir.getId()
        dir.createEntry({'id': 'user1', 'groups': ['group1', 'group2']})
        dir.createEntry({'id': 'user2', 'groups': ['group1', 'group3']})
        dir.createEntry({'id': 'user3', 'groups': []})
        in_group1 = pd._crossGetList(dir_id, 'groups', 'group1')
        self.assertEquals(in_group1, ['user1', 'user2'])
        in_group2 = pd._crossGetList(dir_id, 'groups', 'group2')
        self.assertEquals(in_group2, ['user1'])
        in_group3 = pd._crossGetList(dir_id, 'groups', 'group3')
        self.assertEquals(in_group3, ['user2'])

        # Special cases
        in_group4 = pd._crossGetList(dir.getId(), 'groups', 'group4')
        self.assertEquals(in_group4, [])
        self.assertRaises(KeyError,
                lambda: pd._crossGetList(dir.getId(), 'not_existing', 'group1'))

    def test_crossSetList(self):
        dir, pd = self.dir, self.pd
        dir_id = dir.getId()
        # Initial setting
        dir.createEntry({'id': 'user1', 'groups': ['group1', 'group2']})
        dir.createEntry({'id': 'user2', 'groups': []})
        dir.createEntry({'id': 'user3', 'groups': []})
        # This should not change anything
        pd._crossSetList(dir_id, 'groups', 'group1', ['user1'])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])

        # Adding users to a new group
        pd._crossSetList(dir_id, 'groups', 'group3', ['user1', 'user2'])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group3'),
                                            ['user1', 'user2'])

        # Removing users already in group3
        pd._crossSetList(dir_id, 'groups', 'group3', [])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group3'), [])

        # Unexisting user triggers KeyError
        # XXX: is this the same behavior for all directory backends?
        self.assertRaises(KeyError,
                lambda:pd._crossSetList(dir_id, 'groups', 'group1',
                                        ['fake_user']))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryTool))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
