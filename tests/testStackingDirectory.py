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
        CPSDirectoryTestCase.afterSetUp(self)
        self.login('root')
        self.pd = self.portal.portal_directories
        self.makeDirs()

    def beforeTearDown(self):
        self.logout()
        CPSDirectoryTestCase.beforeTearDown(self)


    def makeDirs(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('sfoo')
        schema.manage_addField('uid', 'CPS String Field')
        schema.manage_addField('moo', 'CPS String Field')
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
        dirstack.manage_changeProperties(schema='sfoo', id_field='uid',
                                         title_field='moo')
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
        fooentry = {'uid': id1, 'moo': 'ouah', 'glop': 'pasglop'}
        barentry = {'uid': id2, 'moo': 'bar', 'glop': 'gulp'}
        barentrystrip = {'uid': id2strip, 'moo': 'bar', 'glop': 'gulp'}
        bazentry = {'uid': id3, 'moo': 'f', 'glop': 'g'}
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
        fooentry = {'uid': id1, 'moo': 'ouah', 'glop': 'pasglop'}
        fooentrystrip = {'uid': id1strip, 'moo': 'ouah', 'glop': 'pasglop'}
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

    def test_listEntryIdsAndTitles(self):
        self.dirfoo.createEntry({'uid': '444', 'moo': '4'}) # nostrip -> ignored
        self.dirfoo.createEntry({'uid': 'a_555', 'moo': '5'})
        self.dirbar.createEntry({'uid': '666', 'moo': '6'})
        self.dirbar.createEntry({'uid': '777_b', 'moo': '7'})
        self.dirbaz.createEntry({'uid': '888', 'moo': '8'})
        okidts = [('a_555', '5'),
                  ('666_b', '6'),
                  ('777_b_b', '7'),
                  ('888', '8')]
        idts = self.dirstack.listEntryIdsAndTitles()
        okidts.sort()
        idts.sort()
        self.assertEquals(idts, okidts)

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

    def test_editEntry_strip(self):
        # Build previous entry in backing dir
        id = 'AAA_b'
        idstrip = 'AAA'
        barentry = {'uid': idstrip, 'moo': 'ff', 'glop': 'gg'}
        self.dirbar.createEntry(barentry)
        # Now change it
        entry = {'uid': id, 'moo': 'MOO'}
        self.dirstack.editEntry(entry)
        # Check changed
        okentry = {'uid': id, 'moo': 'MOO', 'glop': 'gg'}
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, okentry)
        # Check backing dir has changed
        barentry2 = self.dirbar.getEntry(idstrip)
        barentry3 = {'uid': idstrip, 'moo': 'MOO', 'glop': 'gg'}
        self.assertEquals(barentry2, barentry3)

    def test_createEntry_nostrip(self):
        id = 'a_BBB'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': 'oof', 'glop': 'borg'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirfoo.hasEntry(id))
        self.assert_(self.dirstack.hasEntry(id))
        # Check created
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirfoo.getEntry(id)
        fooentry2 = {'uid': id, 'moo': 'oof', 'glop': 'borg'}
        self.assertEquals(fooentry, fooentry2)

    def test_createEntry_strip(self):
        id = 'CCC_b'
        idstrip = 'CCC'
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': 'fifi', 'glop': 'gligli'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(idstrip))
        self.assert_(self.dirstack.hasEntry(id))
        # Check created
        entry2 = self.dirstack.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirbar.getEntry(idstrip)
        fooentry2 = {'uid': idstrip, 'moo': 'fifi', 'glop': 'gligli'}
        self.assertEquals(fooentry, fooentry2)

    def test_deleteEntry_nostrip(self):
        id = 'a_DDD'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirstack.hasEntry(id))
        entry = {'uid': id, 'moo': 'canard', 'glop': 'wc'}
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
        entry = {'uid': id, 'moo': 'canard', 'glop': 'wc'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(idstrip))
        self.assert_(self.dirstack.hasEntry(id))
        self.dirstack.deleteEntry(id)
        self.failIf(self.dirbar.hasEntry(idstrip))
        self.failIf(self.dirstack.hasEntry(id))

    def test_searchEntries(self):
        dir = self.dirstack

        fooentry = {'uid': 'FFF', 'moo': 'f1', 'glop': 'g1'}
        self.dirfoo.createEntry(fooentry)

        entry1 = {'uid': 'a_GGG', 'moo': 'f1', 'glop': 'g1'}
        dir.createEntry(entry1)
        entry2 = {'uid': 'a_HHH', 'moo': 'f2', 'glop': 'g1'}
        dir.createEntry(entry2)
        entry3 = {'uid': 'III_b', 'moo': 'f1', 'glop': 'g1'}
        dir.createEntry(entry3)
        entry4 = {'uid': 'JJJ_b', 'moo': 'f2', 'glop': 'g2'}
        dir.createEntry(entry4)
        entry5 = {'uid': 'KKK', 'moo': 'f1', 'glop': 'g2'}
        dir.createEntry(entry5)
        entry6 = {'uid': 'LLL', 'moo': 'f2', 'glop': 'g2'}
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
        ids = dir.searchEntries(moo='f1')
        ids.sort()
        self.assertEquals(ids, ['III_b', 'KKK', 'a_GGG'])
        # Multi-field search
        ids = dir.searchEntries(moo='f1', glop='g1')
        ids.sort()
        self.assertEquals(ids, ['III_b', 'a_GGG'])
        ids = dir.searchEntries(moo='f1', glop='g2')
        self.assertEquals(ids, ['KKK'])

        # With return_fields
        res = dir.searchEntries(return_fields=['uid'])
        res.sort()
        self.assertEquals(res, [('III_b', {'uid': 'III_b'}),
                                ('JJJ_b', {'uid': 'JJJ_b'}),
                                ('KKK',   {'uid': 'KKK'}),
                                ('LLL',   {'uid': 'LLL'}),
                                ('a_GGG', {'uid': 'a_GGG'}),
                                ('a_HHH', {'uid': 'a_HHH'})])
        res = dir.searchEntries(return_fields=['floppp'])
        res.sort()
        self.assertEquals(res, [('III_b', {}),
                                ('JJJ_b', {}),
                                ('KKK', {}),
                                ('LLL', {}),
                                ('a_GGG', {}),
                                ('a_HHH', {})])

        # XXX should test case where dirfoo has substring search
        # on id, and we searchEntries(uid='a_G')

class TestStackingDirectorySecondaryId(CPSDirectoryTestCase):

    def afterSetUp(self):
        CPSDirectoryTestCase.afterSetUp(self)
        self.login('root')
        self.pd = self.portal.portal_directories
        self.makeDirs()

    def beforeTearDown(self):
        self.logout()
        CPSDirectoryTestCase.beforeTearDown(self)


    def makeDirs(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('sfoo')
        schema.manage_addField('uid', 'CPS String Field')
        schema.manage_addField('moo', 'CPS String Field')
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
        # Here we use a secondary id field: moo
        dirstack.manage_changeProperties(schema='sfoo', id_field='moo',
                                         title_field='glop')
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

    def test_getEntry_secondaryId(self):
        moo1 = 'a_ouah'
        moo2 = 'bar_b'
        moo2strip = 'bar'
        moo3 = 'f'
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo2)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo3)
        fooentry = {'uid': '11', 'moo': moo1, 'glop': 'pasglop'}
        barentry = {'uid': '22', 'moo': moo2, 'glop': 'gulp'}
        barentrystrip = {'uid': '22', 'moo': moo2strip, 'glop': 'gulp'}
        bazentry = {'uid': '33', 'moo': moo3, 'glop': 'g'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentrystrip)
        self.dirbaz.createEntry(bazentry)

        entry = self.dirstack.getEntry(moo1)
        self.assertEquals(entry, fooentry)
        entry = self.dirstack.getEntry(moo2)
        self.assertEquals(entry, barentry)
        entry = self.dirstack.getEntry(moo3)
        self.assertEquals(entry, bazentry)

    def test_getEntry_nostrip_secondaryId(self):
        # Test that if a nostrip backing directory has entries
        # that don't conform to the prefix, they aren't found.
        moo1 = 'a_ouah'
        moo1strip = 'ouah'
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1strip)
        fooentry = {'uid': '11', 'moo': moo1, 'glop': 'pasglop'}
        fooentrystrip = {'uid': '22', 'moo': moo1strip, 'glop': 'pasglop'}
        self.dirfoo.createEntry(fooentrystrip)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1strip)
        # Now test with a proper prefixed entry
        self.dirfoo.createEntry(fooentry)
        entry = self.dirstack.getEntry(moo1)
        self.assertEquals(entry, fooentry)
        self.assertRaises(KeyError, self.dirstack.getEntry, moo1strip)

    def test_listEntryIds_secondaryId(self):
        self.dirfoo.createEntry({'uid': '44', 'moo': 'AA'}) # nostrip -> ignored
        self.dirfoo.createEntry({'uid': '55', 'moo': 'a_BB'})
        self.dirbar.createEntry({'uid': '66', 'moo': 'CC'})
        self.dirbar.createEntry({'uid': '77', 'moo': 'DD_b'})
        self.dirbaz.createEntry({'uid': '88', 'moo': 'EE'})
        okids = ['CC_b', 'DD_b_b', 'EE', 'a_BB']
        ids = self.dirstack.listEntryIds()
        okids.sort()
        ids.sort()
        self.assertEquals(ids, okids)

    def test_listEntryIdsAndTitles_secondaryId(self):
        self.dirfoo.createEntry({'moo': '444', 'uid': 'u4', 'glop': '4'})
        self.dirfoo.createEntry({'moo': 'a_555', 'uid': 'u5', 'glop': '5'})
        self.dirbar.createEntry({'moo': '666', 'uid': 'u6', 'glop': '6'})
        self.dirbar.createEntry({'moo': '777_b', 'uid': 'u7', 'glop': '7'})
        self.dirbaz.createEntry({'moo': '888', 'uid': 'u8', 'glop': '8'})
        okidts = [('a_555', '5'),
                  ('666_b', '6'),
                  ('777_b_b', '7'),
                  ('888', '8')]
        idts = self.dirstack.listEntryIdsAndTitles()
        okidts.sort()
        idts.sort()
        self.assertEquals(idts, okidts)

    def test_hasEntry_secondaryId(self):
        self.dirfoo.createEntry({'uid': '44', 'moo': 'AA'}) # nostrip -> ignored
        self.dirfoo.createEntry({'uid': '55', 'moo': 'a_BB'})
        self.dirbar.createEntry({'uid': '66', 'moo': 'CC'})
        self.dirbar.createEntry({'uid': '77', 'moo': 'DD_b'})
        self.dirbaz.createEntry({'uid': '88', 'moo': 'EE'})
        self.assertEquals(self.dirstack.hasEntry('AA'), 0)
        self.assertEquals(self.dirstack.hasEntry('a_AA'), 0)
        self.assertEquals(self.dirstack.hasEntry('BB'), 0)
        self.assertEquals(self.dirstack.hasEntry('a_BB'), 1)
        self.assertEquals(self.dirstack.hasEntry('CC'), 0)
        self.assertEquals(self.dirstack.hasEntry('CC_b'), 1)
        self.assertEquals(self.dirstack.hasEntry('DD'), 0)
        self.assertEquals(self.dirstack.hasEntry('DD_b'), 0)
        self.assertEquals(self.dirstack.hasEntry('DD_b_b'), 1)
        self.assertEquals(self.dirstack.hasEntry('EE'), 1)

    def test_editEntry_strip_secondaryId(self):
        # Build previous entry in backing dir
        uid = 'UU'
        moo = 'AAA_b'
        moostrip = 'AAA'
        barentry = {'moo': moostrip, 'uid': uid, 'glop': 'gg'}
        self.dirbar.createEntry(barentry)
        self.assert_(self.dirstack.hasEntry(moo))
        # Now change it
        # Note: we don't need to pass the backing id field here,
        # as editEntry does a read first anyway
        entry = {'moo': moo, 'glop': 'HH'}
        self.dirstack.editEntry(entry)
        # Check changed
        okentry = {'moo': moo, 'uid': uid, 'glop': 'HH'}
        entry2 = self.dirstack.getEntry(moo)
        self.assertEquals(entry2, okentry)
        # Check backing dir has changed
        barentry2 = self.dirbar.getEntry(uid)
        barentry3 = {'moo': moostrip, 'uid': uid, 'glop': 'HH'}
        self.assertEquals(barentry2, barentry3)

    def test_editEntry_changebackingid_secondaryId(self):
        # Build previous entry in backing dir
        moo = 'AAA_b'
        moostrip = 'AAA'
        barentry = {'moo': moostrip, 'uid': 'UU', 'glop': 'gg'}
        self.dirbar.createEntry(barentry)
        self.assert_(self.dirstack.hasEntry(moo))
        # Now change the field corresponding to the backing id
        # It would mean that in the backing dir, an entry changes id
        # And that's forbidden for now.
        entry = {'moo': moo, 'uid': 'VV'}
        self.assertRaises(KeyError, self.dirstack.editEntry, entry)
        # XXX Note: if an entry VV already existed, it would have been
        # overwritten... an explicit test would be better

    def test_createEntry_strip_secondaryId(self):
        uid = 'CC'
        moo = 'fifi_b'
        moostrip = 'fifi'
        self.failIf(self.dirbar.hasEntry(uid))
        self.failIf(self.dirstack.hasEntry(moo))
        entry = {'moo': moo, 'uid': uid, 'glop': 'gligli'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(uid))
        self.assert_(self.dirstack.hasEntry(moo))
        # Check created
        entry2 = self.dirstack.getEntry(moo)
        self.assertEquals(entry2, entry)
        # Check backing dir
        fooentry = self.dirbar.getEntry(uid)
        fooentry2 = {'moo': moostrip, 'uid': uid, 'glop': 'gligli'}
        self.assertEquals(fooentry, fooentry2)

    def test_deleteEntry_strip_secondaryId(self):
        uid = 'canard'
        moo = 'EEE_b'
        self.failIf(self.dirbar.hasEntry(uid))
        self.failIf(self.dirstack.hasEntry(moo))
        entry = {'moo': moo, 'uid': uid, 'glop': 'wc'}
        self.dirstack.createEntry(entry)
        self.assert_(self.dirbar.hasEntry(uid))
        self.assert_(self.dirstack.hasEntry(moo))
        self.dirstack.deleteEntry(moo)
        self.failIf(self.dirbar.hasEntry(uid))
        self.failIf(self.dirstack.hasEntry(moo))

    def test_searchEntries_secondaryId(self):
        dir = self.dirstack

        fooentry = {'uid': 'FFF', 'moo': 'f1', 'glop': 'g1'}
        self.dirfoo.createEntry(fooentry)

        entry1 = {'uid': 'GGG', 'moo': 'a_f2', 'glop': 'g1'}
        dir.createEntry(entry1)
        entry2 = {'uid': 'HHH', 'moo': 'a_f3', 'glop': 'g2'}
        dir.createEntry(entry2)
        entry3 = {'uid': 'III', 'moo': 'f4_b', 'glop': 'g1'}
        dir.createEntry(entry3)
        entry4 = {'uid': 'JJJ', 'moo': 'f5_b', 'glop': 'g2'}
        dir.createEntry(entry4)
        entry5 = {'uid': 'KKK', 'moo': 'f6', 'glop': 'g1'}
        dir.createEntry(entry5)
        entry6 = {'uid': 'LLL', 'moo': 'f7', 'glop': 'g2'}
        dir.createEntry(entry6)

        # All
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids, ['a_f2', 'a_f3', 'f4_b', 'f5_b', 'f6', 'f7'])

        # Id back-conversion
        ids = dir.searchEntries(moo='a_f2')
        self.assertEquals(ids, ['a_f2'])
        ids = dir.searchEntries(moo='f4_b')
        self.assertEquals(ids, ['f4_b'])
        ids = dir.searchEntries(moo='f4')
        self.assertEquals(ids, [])
        # Id list match
        ids = dir.searchEntries(moo=['a_f2', 'f4_b'])
        ids.sort()
        self.assertEquals(ids, ['a_f2', 'f4_b'])
        # Single field search
        ids = dir.searchEntries(glop='g1')
        ids.sort()
        self.assertEquals(ids, ['a_f2', 'f4_b', 'f6'])
        # Multi-field search
        ids = dir.searchEntries(uid='JJJ', glop='g2')
        self.assertEquals(ids, ['f5_b'])
        ids = dir.searchEntries(moo='a_f2', glop='g1')
        self.assertEquals(ids, ['a_f2'])

        # With return_fields
        res = dir.searchEntries(return_fields=['glop'])
        res.sort()
        self.assertEquals(res, [('a_f2', {'moo': 'a_f2', 'glop': 'g1'}),
                                ('a_f3', {'moo': 'a_f3', 'glop': 'g2'}),
                                ('f4_b', {'moo': 'f4_b', 'glop': 'g1'}),
                                ('f5_b', {'moo': 'f5_b', 'glop': 'g2'}),
                                ('f6', {'moo': 'f6', 'glop': 'g1'}),
                                ('f7', {'moo': 'f7', 'glop': 'g2'})])

        # XXX should test case where dirfoo has substring search
        # on id, and we searchEntries(uid='a_G')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestStackingDirectory))
    suite.addTest(unittest.makeSuite(TestStackingDirectorySecondaryId))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
