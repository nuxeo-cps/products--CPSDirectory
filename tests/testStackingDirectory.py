# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
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
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing.ZopeTestCase import ZopeTestCase
from AccessControl import Unauthorized
from OFS.Folder import Folder

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot

class TestStackingDirectory(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = FakeDirectoryTool()
        self.portal = self.root.portal
        self.pd = self.portal.portal_directories

    def makeSchema(self):
        stool = self.portal.portal_schemas
        sfoo = FakeSchema({
            'uid': FakeField(),
            'moo': FakeField(),
            'glop': FakeField(),
            })
        stool._setObject('sfoo', sfoo)

    def makeDirs(self):
        from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
        from Products.CPSDirectory.StackingDirectory import StackingDirectory
        dtool = self.portal.portal_directories
        dirfoo = ZODBDirectory('dirfoo', id_field='uid', schema='sfoo')
        dtool._setObject(dirfoo.getId(), dirfoo)
        dirbar = ZODBDirectory('dirbar', id_field='uid', schema='sfoo')
        dtool._setObject(dirbar.getId(), dirbar)
        # In baz, the id is moo.
        dirbaz = ZODBDirectory('dirbaz', id_field='moo', schema='sfoo')
        dtool._setObject(dirbaz.getId(), dirbaz)
        dirstack = StackingDirectory('dirstack', id_field='uid', schema='sfoo',
                title_field='glop',
                backing_dirs=(
                    'dirfoo',
                    'dirbar',
                    'dirbaz',
                    ),
                creation_dir='dirbar',
                )
        dtool._setObject(dirstack.getId(), dirstack)
        for dir in (dirfoo, dirbar, dirbaz, dirstack):
            dir.manage_changeProperties(
                    acl_directory_view_roles='test_role_1_',
                    acl_entry_create_roles='test_role_1_',
                    acl_entry_delete_roles='test_role_1_',
                    acl_entry_view_roles='test_role_1_',
                    acl_entry_edit_roles='test_role_1_',
                    )

        self.dirfoo = dtool.dirfoo
        self.dirbar = dtool.dirbar
        self.dirbaz = dtool.dirbaz
        self.dirstack = dtool.dirstack
        self.dirs = [self.dirfoo, self.dirbar, self.dirbaz]

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDirs()

    def test_getEntry(self):
        id1 = '111'
        id2 = '222'
        id3 = '333'
        bid3 = 'mmm'
        self.assertRaises(KeyError, self.dirstack.getEntry, id1)
        self.assertRaises(KeyError, self.dirstack.getEntry, id2)
        self.assertRaises(KeyError, self.dirstack.getEntry, id3)
        fooentry = {'uid': id1, 'moo': 'ouah', 'glop': 'pasglop'}
        barentry = {'uid': id2, 'moo': 'bar', 'glop': 'gulp'}
        bazentry = {'uid': id3, 'moo': bid3, 'glop': 'g'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        self.dirbaz.createEntry(bazentry)
        entry = self.dirstack.getEntry(id1)
        self.assertEquals(entry, fooentry)
        entry = self.dirstack.getEntry(id2)
        self.assertEquals(entry, barentry)
        entry = self.dirstack.getEntry(id3)
        self.assertEquals(entry, bazentry)

    def test_listEntryIds(self):
        self.dirfoo.createEntry({'uid': '444'})
        self.dirbar.createEntry({'uid': '666'})
        self.dirbaz.createEntry({'uid': '888', 'moo': 'om'})
        okids = ['444', '666', '888']
        ids = self.dirstack.listEntryIds()
        ids.sort()
        self.assertEquals(ids, okids)

    def test_listEntryIdsAndTitles(self):
        self.dirfoo.createEntry({'uid': '444', 'glop': 'pasglop'})
        self.dirbar.createEntry({'uid': '666', 'glop': 'gulp'})
        self.dirbaz.createEntry({'uid': '888', 'moo': 'm8', 'glop': 'g'})
        okidts = [('444', 'pasglop'),
                  ('666', 'gulp'),
                  ('888', 'g')]
        idts = self.dirstack.listEntryIdsAndTitles()
        idts.sort()
        self.assertEquals(idts, okidts)

    def test_hasEntry(self):
        self.dirfoo.createEntry({'uid': '444'})
        self.dirbar.createEntry({'uid': '666'})
        self.dirbaz.createEntry({'uid': '888', 'moo': 'MOO'})
        self.assertEquals(self.dirstack.hasEntry('zzz'), 0)
        self.assertEquals(self.dirstack.hasEntry('444'), 1)
        self.assertEquals(self.dirstack.hasEntry('666'), 1)
        self.assertEquals(self.dirstack.hasEntry('888'), 1)
        self.assertEquals(self.dirstack.hasEntry('MOO'), 0)

    def test_editEntry(self):
        # Build previous entry in backing dir
        id = 'AAA'
        barentry = {'uid': id, 'moo': 'ff', 'glop': 'gg'}
        self.dirbar.createEntry(barentry)
        # Now change it
        entry = {'uid': id, 'moo': 'MOO'}
        self.dirstack.editEntry(entry)
        # Check changed
        okentry = {'uid': id, 'moo': 'MOO', 'glop': 'gg'}
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, okentry)
        # Check backing dir has changed
        barentry2 = self.dirbar.getEntry(id)
        self.assertEquals(barentry2, okentry)

    def test_editEntry_secondary(self):
        # Build previous entry in backing dir
        id = 'AAA'
        bid = 'moog'
        bazentry = {'uid': id, 'moo': bid, 'glop': 'gg'}
        self.dirbaz.createEntry(bazentry)
        # Now change it
        entry = {'uid': id, 'moo': bid, 'glop': 'gulp'}
        self.dirstack.editEntry(entry)
        # Check changed
        okentry = {'uid': id, 'moo': bid, 'glop': 'gulp'}
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, okentry)
        # Check backing dir has changed
        bazentry2 = self.dirbaz.getEntry(bid)
        self.assertEquals(bazentry2, okentry)

    def test_createEntry(self):
        id = 'CCC'
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': 'fifi', 'glop': 'gligli'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(id))
        self.assert_(self.dirstack.hasEntry(id))
        # Check created
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirbar.getEntry(id)
        self.assertEquals(fooentry, entry)

    def test_deleteEntry(self):
        id = 'DDD'
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': 'canard', 'glop': 'wc'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(id))
        self.assert_(self.dirstack.hasEntry(id))
        self.dirstack.deleteEntry(id)
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))

    def test_deleteEntry_secondary(self):
        id = 'DDD'
        bid = 'dog'
        self.failIf(self.dirbaz.hasEntry(bid))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': bid, 'glop': 'cat'}
        self.dirbaz.createEntry(entry)
        self.assert_(self.dirbaz.hasEntry(bid))
        self.assert_(self.dirstack.hasEntry(id))
        self.dirstack.deleteEntry(id)
        self.failIf(self.dirbaz.hasEntry(bid))
        self.failIf(self.dirstack.hasEntry(id))

    def test_searchEntries(self):
        dir = self.dirstack

        entry1 = {'uid': 'GGG', 'moo': 'f2', 'glop': 'g1'}
        self.dirfoo.createEntry(entry1)
        entry2 = {'uid': 'HHH', 'moo': 'f3', 'glop': 'g2'}
        self.dirfoo.createEntry(entry2)
        entry3 = {'uid': 'III', 'moo': 'f4', 'glop': 'g1'}
        self.dirbar.createEntry(entry3)
        entry4 = {'uid': 'JJJ', 'moo': 'f5', 'glop': 'g2'}
        self.dirbar.createEntry(entry4)
        entry5 = {'uid': 'KKK', 'moo': 'f6', 'glop': 'g1'}
        self.dirbaz.createEntry(entry5)
        entry6 = {'uid': 'LLL', 'moo': 'f7', 'glop': 'g2'}
        self.dirbaz.createEntry(entry6)

        # All
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids, ['GGG', 'HHH', 'III', 'JJJ', 'KKK', 'LLL'])

        # uid
        ids = dir.searchEntries(uid='GGG')
        self.assertEquals(ids, ['GGG'])
        ids = dir.searchEntries(uid='III')
        self.assertEquals(ids, ['III'])
        ids = dir.searchEntries(uid='LLL')
        self.assertEquals(ids, ['LLL'])
        ids = dir.searchEntries(uid='f7')
        self.assertEquals(ids, [])

        # attribute
        ids = dir.searchEntries(moo='f2')
        self.assertEquals(ids, ['GGG'])
        ids = dir.searchEntries(moo='f5')
        self.assertEquals(ids, ['JJJ'])
        ids = dir.searchEntries(moo='f6') # secondary id
        self.assertEquals(ids, ['KKK'])
        ids = dir.searchEntries(moo='LLL')
        self.assertEquals(ids, [])

        # Multiple results
        # Id list match
        ids = dir.searchEntries(moo=['f2', 'f7'])
        ids.sort()
        self.assertEquals(ids, ['GGG', 'LLL'])
        # Single field search
        ids = dir.searchEntries(glop='g1')
        ids.sort()
        self.assertEquals(ids, ['GGG', 'III', 'KKK'])
        # Multi-field search
        ids = dir.searchEntries(uid='JJJ', glop='g2')
        self.assertEquals(ids, ['JJJ'])
        ids = dir.searchEntries(moo='f3', glop='g2')
        self.assertEquals(ids, ['HHH'])
        # With secondary id
        ids = dir.searchEntries(uid='KKK', glop='g1')
        self.assertEquals(ids, ['KKK'])
        ids = dir.searchEntries(moo='f7', glop='g2')
        self.assertEquals(ids, ['LLL'])
        ids = dir.searchEntries(moo='f7', uid='LLL')
        self.assertEquals(ids, ['LLL'])

        # With return_fields
        res = dir.searchEntries(return_fields=['glop'])
        res.sort()
        self.assertEquals(res, [('GGG', {'glop': 'g1'}),
                                ('HHH', {'glop': 'g2'}),
                                ('III', {'glop': 'g1'}),
                                ('JJJ', {'glop': 'g2'}),
                                ('KKK', {'uid': 'KKK', 'glop': 'g1'}),
                                ('LLL', {'uid': 'LLL', 'glop': 'g2'})])

        # With all return fields
        res = dir.searchEntries(glop='g2', return_fields=['*'])
        res.sort()
        self.assertEquals(res, [('HHH', entry2),
                                ('JJJ', entry4),
                                ('LLL', entry6)])

    def testBasicSecurity(self):
        self.assert_(self.dirstack.searchEntries() is not None)
        self.logout()
        self.assertRaises(Unauthorized, self.dirstack.searchEntries)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStackingDirectory))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
