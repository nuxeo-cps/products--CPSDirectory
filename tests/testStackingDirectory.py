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
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase


class TestStackingDirectory(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('root')
        self.pd = self.portal.portal_directories
        self.makeDirs()

    def beforeTearDown(self):
        self.logout()


    def makeDirs(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('sfoo')
        schema.manage_addField('uid', 'CPS String Field')
        schema.manage_addField('foo', 'CPS String Field')
        schema.manage_addField('glop', 'CPS String Field')

        dirfoo = self.pd.manage_addCPSDirectory('dirfoo',
                                                'CPS ZODB Directory')
        dirfoo.manage_changeProperties(schema='sfoo', id_field='uid')

        dirbar = self.pd.manage_addCPSDirectory('dirbar',
                                                'CPS ZODB Directory')
        dirbar.manage_changeProperties(schema='sfoo', id_field='uid')

        dirbaz = self.pd.manage_addCPSDirectory('dirbaz',
                                                'CPS ZODB Directory')
        dirbaz.manage_changeProperties(schema='sfoo', id_field='uid')

        dirstack = self.pd.manage_addCPSDirectory('dirstack',
                                                  'CPS Stacking Directory')
        dirstack.manage_changeProperties(schema='sfoo', id_field='uid')
        dirstack.setBackingDirectories(
            (# dir_id, style, prefix/suffix, strip
            ('dirfoo', 'prefix', 'a_', 0),
            ('dirbar', 'suffix', '_b', 1),
            ('dirbaz', 'none', None, 0),
            ))

        self.dirfoo = dirfoo
        self.dirbar = dirbar
        self.dirbaz = dirbaz
        self.dirstack = dirstack

    def test_getEntry(self):
        id1 = 'a_111'
        id2 = '222_b'
        id2strip = '222'
        id3 = '333'
        self.assertRaises(KeyError, self.dirstack.getEntry, id1)
        self.assertRaises(KeyError, self.dirstack.getEntry, id2)
        self.assertRaises(KeyError, self.dirstack.getEntry, id3)
        fooentry = {'uid': id1, 'foo': 'ouah', 'glop': 'pasglop'}
        barentry = {'uid': id2, 'foo': 'bar', 'glop': 'gulp'}
        barentrystrip = {'uid': id2strip, 'foo': 'bar', 'glop': 'gulp'}
        bazentry = {'uid': id3, 'foo': 'f', 'glop': 'g'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentrystrip)
        self.dirbaz.createEntry(bazentry)
        entry = self.dirstack.getEntry(id1)
        self.assertEquals(entry, fooentry)
        entry = self.dirstack.getEntry(id2)
        self.assertEquals(entry, barentry)
        entry = self.dirstack.getEntry(id3)
        self.assertEquals(entry, bazentry)

    def test_getEntry_nostrip(self):
        # Test that if a nostrip backing directory has entries
        # that don't conform to the prefix, they aren't found.
        id1 = 'a_111'
        id1strip = '111'
        self.assertRaises(KeyError, self.dirstack.getEntry, id1)
        self.assertRaises(KeyError, self.dirstack.getEntry, id1strip)
        fooentry = {'uid': id1, 'foo': 'ouah', 'glop': 'pasglop'}
        fooentrystrip = {'uid': id1strip, 'foo': 'ouah', 'glop': 'pasglop'}
        self.dirfoo.createEntry(fooentrystrip)
        self.assertRaises(KeyError, self.dirstack.getEntry, id1)
        self.assertRaises(KeyError, self.dirstack.getEntry, id1strip)
        # Now test with a proper prefixed entry
        self.dirfoo.createEntry(fooentry)
        entry = self.dirstack.getEntry(id1)
        self.assertEquals(entry, fooentry)
        self.assertRaises(KeyError, self.dirstack.getEntry, id1strip)

    def test_listEntryIds(self):
        self.dirfoo.createEntry({'uid': '444'}) # nostrip -> ignored
        self.dirfoo.createEntry({'uid': 'a_555'})
        self.dirbar.createEntry({'uid': '666'})
        self.dirbar.createEntry({'uid': '777_b'})
        self.dirbaz.createEntry({'uid': '888'})
        okids = ['a_555', '666_b', '777_b_b', '888']
        ids = self.dirstack.listEntryIds()
        okids.sort()
        ids.sort()
        self.assertEquals(ids, okids)

    def test_hasEntry(self):
        self.dirfoo.createEntry({'uid': '444'}) # nostrip -> ignored
        self.dirfoo.createEntry({'uid': 'a_555'})
        self.dirbar.createEntry({'uid': '666'})
        self.dirbar.createEntry({'uid': '777_b'})
        self.dirbaz.createEntry({'uid': '888'})
        self.assertEquals(self.dirstack.hasEntry('444'), 0)
        self.assertEquals(self.dirstack.hasEntry('a_444'), 0)
        self.assertEquals(self.dirstack.hasEntry('555'), 0)
        self.assertEquals(self.dirstack.hasEntry('a_555'), 1)
        self.assertEquals(self.dirstack.hasEntry('666'), 0)
        self.assertEquals(self.dirstack.hasEntry('666_b'), 1)
        self.assertEquals(self.dirstack.hasEntry('777'), 0)
        self.assertEquals(self.dirstack.hasEntry('777_b'), 0)
        self.assertEquals(self.dirstack.hasEntry('777_b_b'), 1)
        self.assertEquals(self.dirstack.hasEntry('888'), 1)

    def test_editEntry(self):
        # Build previous entry in backing dir
        id = 'AAA_b'
        idstrip = 'AAA'
        barentry = {'uid': idstrip, 'foo': 'ff', 'glop': 'gg'}
        self.dirbar.createEntry(barentry)
        # Now change it
        entry = {'uid': id, 'foo': 'FOO'}
        self.dirstack.editEntry(entry)
        # Check changed
        okentry = {'uid': id, 'foo': 'FOO', 'glop': 'gg'}
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, okentry)
        # Check backing dir has changed
        barentry2 = self.dirbar.getEntry(idstrip)
        barentry3 = {'uid': idstrip, 'foo': 'FOO', 'glop': 'gg'}
        self.assertEquals(barentry2, barentry3)

    def test_createEntry_nostrip(self):
        id = 'a_BBB'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'foo': 'oof', 'glop': 'borg'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirfoo.hasEntry(id))
        self.assert_(self.dirstack.hasEntry(id))
        # Check created
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirfoo.getEntry(id)
        fooentry2 = {'uid': id, 'foo': 'oof', 'glop': 'borg'}
        self.assertEquals(fooentry, fooentry2)

    def test_createEntry_strip(self):
        id = 'CCC_b'
        idstrip = 'CCC'
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'foo': 'fifi', 'glop': 'gligli'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(idstrip))
        self.assert_(self.dirstack.hasEntry(id))
        # Check created
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirbar.getEntry(idstrip)
        fooentry2 = {'uid': idstrip, 'foo': 'fifi', 'glop': 'gligli'}
        self.assertEquals(fooentry, fooentry2)

    def test_deleteEntry_nostrip(self):
        id = 'a_DDD'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'foo': 'canard', 'glop': 'wc'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirfoo.hasEntry(id))
        self.assert_(self.dirstack.hasEntry(id))
        self.dirstack.deleteEntry(id)
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))

    def test_deleteEntry_strip(self):
        id = 'EEE_b'
        idstrip = 'EEE'
        self.failIf(self.dirbar.hasEntry(idstrip))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'foo': 'canard', 'glop': 'wc'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(idstrip))
        self.assert_(self.dirstack.hasEntry(id))
        self.dirstack.deleteEntry(id)
        self.failIf(self.dirbar.hasEntry(idstrip))
        self.failIf(self.dirstack.hasEntry(id))

    def test_searchEntries(self):
        dir = self.dirstack

        fooentry = {'uid': 'FFF', 'foo': 'f1', 'glop': 'g1'}
        self.dirfoo.createEntry(fooentry)

        entry1 = {'uid': 'a_GGG', 'foo': 'f1', 'glop': 'g1'}
        dir.createEntry(entry1)
        entry2 = {'uid': 'a_HHH', 'foo': 'f2', 'glop': 'g1'}
        dir.createEntry(entry2)
        entry3 = {'uid': 'III_b', 'foo': 'f1', 'glop': 'g1'}
        dir.createEntry(entry3)
        entry4 = {'uid': 'JJJ_b', 'foo': 'f2', 'glop': 'g2'}
        dir.createEntry(entry4)
        entry5 = {'uid': 'KKK', 'foo': 'f1', 'glop': 'g2'}
        dir.createEntry(entry5)
        entry6 = {'uid': 'LLL', 'foo': 'f2', 'glop': 'g2'}
        dir.createEntry(entry6)

        # All
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids,
                          ['III_b', 'JJJ_b', 'KKK', 'LLL', 'a_GGG', 'a_HHH'])

        # Id back-conversion
        ids = dir.searchEntries(uid='a_GGG')
        self.assertEquals(ids, ['a_GGG'])
        ids = dir.searchEntries(uid='III_b')
        self.assertEquals(ids, ['III_b'])
        ids = dir.searchEntries(uid='III')
        self.assertEquals(ids, [])
        # Id list match
        ids = dir.searchEntries(uid=['a_GGG', 'III_b'])
        ids.sort()
        self.assertEquals(ids, ['III_b', 'a_GGG'])
        # Single field search
        ids = dir.searchEntries(foo='f1')
        ids.sort()
        self.assertEquals(ids, ['III_b', 'KKK', 'a_GGG'])
        # Multi-field search
        ids = dir.searchEntries(foo='f1', glop='g1')
        ids.sort()
        self.assertEquals(ids, ['III_b', 'a_GGG'])
        ids = dir.searchEntries(foo='f1', glop='g2')
        self.assertEquals(ids, ['KKK'])

        # XXX check with field_ids

        # XXX should test case where foodir has substring search
        # on id, and we searchEntries(uid='a_G')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStackingDirectory))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
