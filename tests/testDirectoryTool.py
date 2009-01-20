# Copyright 2005-2007 Nuxeo SAS <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

import os, sys

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import Unauthorized
from OFS.Folder import Folder

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeUserFolder
from Products.CPSDirectory.tests.fakeCps import FakeRoot

from Products.CPSDirectory.DirectoryTool import DirectoryTool
from Products.CPSDirectory.FieldNamespace import crossGetList
from Products.CPSDirectory.FieldNamespace import crossSetList

class TestDirectoryTool(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.acl_users = FakeUserFolder()
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

        self.pd.members.hidden_in_navigation = True
        dir_list = self.pd.listVisibleDirectories()
        self.assertEquals(dir_list, [])

    def test_crossGetList(self):
        # crossGetList is a utility function that should be registered on the
        # CPSSchemas.FieldNamespace.util object but we can test it directly on
        # the fake portal object as well
        dir, portal = self.dir, self.portal
        dir_id = dir.getId()
        dir.createEntry({'id': 'user1', 'groups': ['group1', 'group2']})
        dir.createEntry({'id': 'user2', 'groups': ['group1', 'group3']})
        dir.createEntry({'id': 'user3', 'groups': []})
        in_group1 = crossGetList(portal, dir_id, 'groups', 'group1')
        self.assertEquals(in_group1, ['user1', 'user2'])
        in_group2 = crossGetList(portal, dir_id, 'groups', 'group2')
        self.assertEquals(in_group2, ['user1'])
        in_group3 = crossGetList(portal, dir_id, 'groups', 'group3')
        self.assertEquals(in_group3, ['user2'])

        # Special cases
        in_group4 = crossGetList(portal, dir.getId(), 'groups', 'group4')
        self.assertEquals(in_group4, [])
        self.assertRaises(KeyError,
            lambda: crossGetList(portal, dir.getId(), 'not_existing', 'group1'))

    def test_crossSetList(self):
        # crossSetList is a utility function that should be registered on the
        # CPSSchemas.FieldNamespace.util object but we can test it directly on
        # the fake portal object as well
        dir, portal = self.dir, self.portal
        dir_id = dir.getId()
        # Initial setting
        dir.createEntry({'id': 'user1', 'groups': ['group1', 'group2']})
        dir.createEntry({'id': 'user2', 'groups': []})
        dir.createEntry({'id': 'user3', 'groups': []})
        # This should not change anything
        crossSetList(portal, dir_id, 'groups', 'group1', ['user1'])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])

        # Adding users to a new group
        crossSetList(portal, dir_id, 'groups', 'group3', ['user1', 'user2'])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group3'),
                                            ['user1', 'user2'])

        # Removing users already in group3
        crossSetList(portal, dir_id, 'groups', 'group3', [])
        self.assertEquals(dir.searchEntries(groups='group1'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group2'), ['user1'])
        self.assertEquals(dir.searchEntries(groups='group3'), [])

        # Regression test for bug #1265 (tuple safeness)
        dir.createEntry({'id': 'iliketuples', 'groups': ('group2',)})
        # removing user1 out of group1 and putting iliketuples instead
        crossSetList(portal, dir_id, 'groups', 'group1', ['iliketuples'])
        self.assertEquals(dir.searchEntries(groups='group1'), ['iliketuples'])
        self.assertEquals(dir.searchEntries(groups='group2'),
                          ['iliketuples', 'user1'])

        # 'value_search': cases where _searchEntries is decorelated from
        # _getEntry
        # patching searches to have them behave differently from gets
        normal_searchEntries = dir._searchEntries
        def _searchEntries(**kw):
            groups = kw.get('groups')
            if groups is not None:
                if isinstance(groups, basestring):
                    groups = [groups]
                kw['groups'] = [group.split('=')[1] for group in groups]
            return normal_searchEntries(**kw)
        dir._searchEntries = _searchEntries
        # testing the patch
        self.assertEquals(dir.searchEntries(groups='ou=group1'), ['iliketuples'])
        self.assertEquals(dir.searchEntries(groups='ou=group2'),
                          ['iliketuples', 'user1'])
        self.assertRaises(IndexError, dir.searchEntries, groups='group2')
        # do test: keep user1, remove iliketuples, adding user2
        crossSetList(portal, dir_id, 'groups', 'group2', ['user1', 'user2'],
                     value_search='ou=group2')
        self.assertEquals(dir.searchEntries(groups='ou=group2'),
                          ['user1', 'user2'])
        # unpatching
        dir._searchEntries = normal_searchEntries

        # Unexisting user triggers KeyError
        # XXX: is this the same behavior for all directory backends?
        self.assertRaises(KeyError,
                lambda:crossSetList(portal, dir_id, 'groups', 'group1',
                                        ['fake_user']))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryTool))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
