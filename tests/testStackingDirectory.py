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

    def xxxtestSearch(self):
        dir = self.dir

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'idd': id1, 'foo': foo1, 'bar': bar1}
        dir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'idd': id2, 'foo': foo2, 'bar': bar2}
        dir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### Without substrings
        dir.search_substring_fields = []

        # Basic searches
        res = dir.searchEntries(idd=id1)
        self.assertEquals(res, [id1])
        res = dir.searchEntries(idd=[id1])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=foo1)
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=[foo1])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar='a123')
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar=['a123'])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [id1])

        # Multi-field searches
        res = dir.searchEntries(idd=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [id2])
        res = dir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [id1])

        # Failing substring searches
        res = dir.searchEntries(idd='re')
        self.assertEquals(res, [])
        res = dir.searchEntries(idd='TREE')
        self.assertEquals(res, [])
        res = dir.searchEntries(foo='e')
        self.assertEquals(res, [])
        res = dir.searchEntries(bar='812a')
        self.assertEquals(res, [])
        res = dir.searchEntries(bar='gr')
        self.assertEquals(res, [])
        res = dir.searchEntries(bar=['gr'])
        self.assertEquals(res, [])
        res = dir.searchEntries(foo='E', bar='12')
        self.assertEquals(res, [])

    def xxxtestSearchSubstrings(self):
        dir = self.dir

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'idd': id1, 'foo': foo1, 'bar': bar1}
        dir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'idd': id2, 'foo': foo2, 'bar': bar2}
        dir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### With substrings
        dir.search_substring_fields = ['foo', 'bar']

        # Basic searches
        res = dir.searchEntries(idd=id1)
        self.assertEquals(res, [id1])
        res = dir.searchEntries(idd=[id1])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=foo1)
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=[foo1])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar='a123')
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar=['a123'])
        self.assertEquals(res, [id1])
        res = dir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [id1])

        # Multi-field searches
        res = dir.searchEntries(idd=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [id2])
        res = dir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [id1])

        # Substring searches
        res = dir.searchEntries(idd='re')
        self.assertEquals(res, [])
        res = dir.searchEntries(idd='TREE')
        self.assertEquals(res, [])
        res = dir.searchEntries(foo='e')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar='812a')
        self.assertEquals(res, [id2])
        res = dir.searchEntries(bar='gr')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['gr'])
        self.assertEquals(res, [])
        res = dir.searchEntries(foo='E', bar='12')
        self.assertEquals(res, ids)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStackingDirectory))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
