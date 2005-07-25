# Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from OFS.Folder import Folder

from Products.CPSDirectory.tests.fakeSQL import FakeSQLConnection
from Products.CPSDirectory.tests.fakeSQL import FakeDBC
from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot



class TestSQLDirectory(ZopeTestCase):

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()
        self.makeTable()

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = FakeDirectoryTool()
        self.root.portal.sqlconn = FakeSQLConnection('sqlconn')
        self.portal = self.root.portal

    def makeSchema(self):
        stool = self.portal.portal_schemas
        s = FakeSchema({
            'uid': FakeField(),
            'givenName': FakeField(),
            'sn': FakeField(),
            })
        stool._setObject('members', s)

    def makeDir(self):
        from Products.CPSDirectory.SQLDirectory import SQLDirectory
        dtool = self.portal.portal_directories
        dir = SQLDirectory('sqldir',
                           id_field='uid',
                           schema='members',
                           schema_search='',
                           layout='',
                           layout_search='',
                           password_field='',
                           title_field='givenName',
                           acl_directory_view_roles='test_role_1_',
                           acl_entry_create_roles='test_role_1_',
                           acl_entry_delete_roles='test_role_1_',
                           acl_entry_view_roles='test_role_1_',
                           acl_entry_edit_roles='test_role_1_',
                           sql_connection_path='/portal/sqlconn',
                           sql_table='people',
                           )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.sqldir

    def makeTable(self):
        sqlconn = self.portal.sqlconn
        sqlconn._createTable('people', ('uid', 'givenName', 'sn'))

    def makeEntries(self):
        dir = self.dir
        entry = {'uid': 'sman', 'givenName': 'Super', 'sn': 'Man'}
        dir.createEntry(entry)
        entry = {'uid': 'batman', 'givenName': 'Bat', 'sn': 'Man'}
        dir.createEntry(entry)

    def test_empty(self):
        dir = self.dir
        self.assertEqual(dir.listEntryIds(), [])
        self.assert_(not dir.hasEntry('foobar'))
        self.assertRaises(KeyError, dir.getEntry, 'foobar')

    def test_createEntry(self):
        self.makeEntries()
        dir = self.dir
        self.assertRaises(KeyError, dir.createEntry,
                          {'uid': 'sman', 'givenName': 'Ha', 'sn': 'Haa'})
        self.assertEqual(dir.listEntryIds(), ['sman', 'batman'])

    def test_deleteEntry(self):
        self.makeEntries()
        dir = self.dir
        dir.deleteEntry('sman')
        self.assert_(not dir.hasEntry('sman'))
        self.assertRaises(KeyError, dir.getEntry, 'sman')
        self.assertEqual(dir.listEntryIds(), ['batman'])
        dir.deleteEntry('batman')
        self.assertEqual(dir.listEntryIds(), [])

    def test_searchEntries(self):
        self.makeEntries()
        dir = self.dir
        # Basic searches
        res = dir.searchEntries(uid='sman')
        self.assertEquals(res, ['sman'])
        res = dir.searchEntries(uid=['sman'])
        self.assertEquals(res, ['sman'])
        res = dir.searchEntries(givenName='Super')
        self.assertEquals(res, ['sman'])
        res = dir.searchEntries(givenName='Blob')
        self.assertEquals(res, [])
        res = dir.searchEntries(givenName=['Super', 'Blob'])
        self.assertEquals(res, ['sman'])
        res = dir.searchEntries(givenName=['Super', 'Bat'])
        self.assertEquals(res, ['sman', 'batman'])
        res = dir.searchEntries(sn='Man')
        self.assertEquals(res, ['sman', 'batman'])
        res = dir.searchEntries(sn=['Man'])
        self.assertEquals(res, ['sman', 'batman'])
        res = dir.searchEntries(sn=['Man', 'Blob'])
        self.assertEquals(res, ['sman', 'batman'])

    def test_listEntryIdsAndTitles(self):
        self.makeEntries()
        dir = self.dir
        res = dir.listEntryIdsAndTitles()
        self.assertEquals(res, [('sman', 'Super'), ('batman', 'Bat')])

    def test_editEntry(self):
        dir = self.dir
        entry = {'uid': 'sman', 'givenName': 'Super', 'sn': 'Man'}
        dir.createEntry(entry)
        dir.editEntry({'uid': 'sman', 'givenName': 'Invisible'})
        self.assertEquals(dir.listEntryIds(), ['sman'])
        res = dir.getEntry('sman')
        self.assertEquals(res, {'uid': 'sman', 'givenName': 'Invisible',
                                'sn': 'Man'})

def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(TestSQLDirectory),
        ))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())


