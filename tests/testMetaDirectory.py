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
from AccessControl import Unauthorized

class TestMetaDirectory(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('manager')
        self.pd = self.portal.portal_directories
        self.makeDirs()

    def beforeTearDown(self):
        self.logout()


    def makeDirs(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('sfoo')
        schema.manage_addField('idd', 'CPS String Field') # different id
        schema.manage_addField('foo', 'CPS String Field') # kept
        schema.manage_addField('pasglop', 'CPS String Field') # ignored

        schema = stool.manage_addCPSSchema('sbar')
        schema.manage_addField('id', 'CPS String Field') # same id
        schema.manage_addField('bar', 'CPS String Field') # kept
        schema.manage_addField('mail', 'CPS String Field') # renamed

        schema = stool.manage_addCPSSchema('smeta')
        schema.manage_addField('id', 'CPS String Field')
        schema.manage_addField('foo', 'CPS String Field')
        schema.manage_addField('bar', 'CPS String Field')
        schema.manage_addField('email', 'CPS String Field')

        dirfoo = self.pd.manage_addCPSDirectory('dirfoo',
                                                'CPS ZODB Directory')
        dirfoo.manage_changeProperties(schema='sfoo', id_field='idd')

        dirbar = self.pd.manage_addCPSDirectory('dirbar',
                                                'CPS ZODB Directory')
        dirbar.manage_changeProperties(schema='sbar', id_field='id')

        dirmeta = self.pd.manage_addCPSDirectory('dirmeta',
                                                 'CPS Meta Directory')
        dirmeta.manage_changeProperties(schema='smeta', id_field='id',
                                        title_field='bar')
        dirmeta.setBackingDirectories(
            ({'dir_id': 'dirfoo',
              'id_conv': None,
              'field_ignore': ('pasglop',),
              },
             {'dir_id': 'dirbar',
              'id_conv': None,
              'field_rename': {'mail': 'email'}, # back:meta
              },
             ))

        self.dirfoo = dirfoo
        self.dirbar = dirbar
        self.dirmeta = dirmeta


    def test_getEntry(self):
        id = '000'
        self.assertRaises(KeyError, self.dirmeta.getEntry, id)
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        okentry = {'id': id, 'foo': 'ouah', 'bar': 'brr', 'email': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        entry = self.dirmeta.getEntry(id)
        self.assertEquals(entry, okentry)

    def test_listEntryIds(self):
        id = '111'
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        id = '222'
        fooentry = {'idd': id, 'foo': 'f', 'pasglop': 'p'}
        barentry = {'id': id, 'bar': 'b', 'mail': 'm'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        okids = ('111', '222')
        ids = self.dirmeta.listEntryIds()
        ids.sort()
        self.assertEquals(okids, tuple(ids))

    def test_listEntryIdsAndTitles(self):
        id = '111'
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        id = '222'
        fooentry = {'idd': id, 'foo': 'f', 'pasglop': 'p'}
        barentry = {'id': id, 'bar': 'b', 'mail': 'm'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        res = self.dirmeta.listEntryIdsAndTitles()
        okres = [('111', 'brr'), ('222', 'b')]
        res.sort()
        self.assertEquals(okres, res)

    def test_hasEntry(self):
        id = '333'
        self.failIf(self.dirmeta.hasEntry(id))
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        self.assert_(self.dirmeta.hasEntry(id))

    def test_editEntry(self):
        # Build previous entry in backing dir
        id = '444'
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        # Now change it
        entry = {'id': id, 'foo': 'FOO', 'bar': 'BAR', 'email': 'EMAIL@COM'}
        self.dirmeta.editEntry(entry)
        # Check changed
        entry2 = self.dirmeta.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dirs have changed
        fooentry2 = self.dirfoo.getEntry(id)
        barentry2 = self.dirbar.getEntry(id)
        fooentry3 = {'idd': id, 'foo': 'FOO', 'pasglop': 'arg'}
        barentry3 = {'id': id, 'bar': 'BAR', 'mail': 'EMAIL@COM'}
        self.assertEquals(fooentry2, fooentry3)
        self.assertEquals(barentry2, barentry3)

    def test_createEntry(self):
        id = '555'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirmeta.hasEntry(id))
        entry = {'id': id, 'foo': 'oof', 'bar': 'rab', 'email': 'lame@at'}
        self.dirmeta.createEntry(entry)
        self.assert_(self.dirfoo.hasEntry(id))
        self.assert_(self.dirbar.hasEntry(id))
        self.assert_(self.dirmeta.hasEntry(id))
        # Check created
        entry2 = self.dirmeta.getEntry(id)
        self.assertEquals(entry2, entry)
        # Check backing dirs
        fooentry = self.dirfoo.getEntry(id)
        barentry = self.dirbar.getEntry(id)
        fooentry2 = {'idd': id, 'foo': 'oof', 'pasglop': ''}
        barentry2 = {'id': id, 'bar': 'rab', 'mail': 'lame@at'}
        self.assertEquals(fooentry, fooentry2)
        self.assertEquals(barentry, barentry2)

    def test_deleteEntry(self):
        id = '666'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirmeta.hasEntry(id))
        entry = {'id': id, 'foo': 'f', 'bar': 'b', 'email': 'e@m'}
        self.dirmeta.createEntry(entry)
        self.assert_(self.dirfoo.hasEntry(id))
        self.assert_(self.dirbar.hasEntry(id))
        self.assert_(self.dirmeta.hasEntry(id))
        self.dirmeta.deleteEntry(id)
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirmeta.hasEntry(id))

    def test_searchEntries(self):
        dir = self.dirmeta

        entry1 = {'id': 'AAA', 'foo': 'oof', 'bar': 'rab', 'email': 'lame@at'}
        dir.createEntry(entry1)
        entry2 = {'id': 'BBB', 'foo': 'oo', 'bar': 'man', 'email': 'evil@hell'}
        dir.createEntry(entry2)
        entry3 = {'id': 'CCC', 'foo': 'oo', 'bar': 'rab', 'email': 'yo@mama'}
        dir.createEntry(entry3)

        # Simple
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC'])

        ids = dir.searchEntries(id='AAA')
        self.assertEquals(ids, ['AAA'])
        ids = dir.searchEntries(foo='oo')
        ids.sort()
        self.assertEquals(ids, ['BBB', 'CCC'])
        ids = dir.searchEntries(bar='rab')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'CCC'])
        ids = dir.searchEntries(hooooole='ohle')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC'])
        ids = dir.searchEntries(email='evil@hell')
        self.assertEquals(ids, ['BBB'])

        # With field_ids
        res = dir.searchEntries(return_fields=['email'])
        res.sort()
        self.assertEquals(res, [('AAA', {'email': 'lame@at'}),
                                ('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'})])
        res = dir.searchEntries(foo='oo', return_fields=['email', 'pasglop'])
        res.sort()
        self.assertEquals(res, [('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'})])
        res = dir.searchEntries(email='lame@at', return_fields=['foo'])
        self.assertEquals(res, [('AAA', {'foo': 'oof'})])

        res = dir.searchEntries(foo='oof', return_fields=['id'])
        self.assertEquals(res, [('AAA', {'id': 'AAA'})])

        # Not strictly defined but test it anyway
        res = dir.searchEntries(return_fields=['blort'])
        res.sort()
        self.assertEquals(res, [('AAA', {}), ('BBB', {}), ('CCC', {})])
        res = dir.searchEntries(return_fields=['id'])
        res.sort()
        self.assertEquals(res, [('AAA', {'id':'AAA'}),
                                ('BBB', {'id':'BBB'}),
                                ('CCC', {'id':'CCC'})])

        # Fields coming from both dirs
        res = dir.searchEntries(foo='oo', return_fields=['email', 'foo'])
        res.sort()
        self.assertEquals(res, [('BBB', {'foo': 'oo', 'email': 'evil@hell'}),
                                ('CCC', {'foo': 'oo', 'email': 'yo@mama'})])

        # All return fields
        res = dir.searchEntries(foo='oo', return_fields=['*'])
        res.sort()
        self.assertEquals(res, [('BBB', entry2),
                                ('CCC', entry3)])

    def test_searchEntries_ghost(self):
        dir = self.dirmeta
        fooentry = {'idd': 'DDD', 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': 'DDD', 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        entry = {'id': 'EEE', 'foo': 'bli', 'bar': 'bot', 'email': 'me@me'}
        dir.createEntry(entry)

        ids = dir.searchEntries(pasglop='blblbl')
        self.assertEquals(ids, ['DDD', 'EEE'])
        res = dir.searchEntries(pasglop='arg', return_fields=['pasglop'])
        res.sort()
        self.assertEquals(res, [('DDD', {}), ('EEE', {})])

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

class TestMetaDirectoryMissing(CPSDirectoryTestCase):

    def afterSetUp(self):
        self.login('manager')
        self.pd = self.portal.portal_directories
        self.makeDirs()

    def beforeTearDown(self):
        self.logout()


    def makeDirs(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('sfoo')
        schema.manage_addField('idd', 'CPS String Field') # different id
        schema.manage_addField('foo', 'CPS String Field') # kept
        schema.manage_addField('pasglop', 'CPS String Field') # ignored

        schema = stool.manage_addCPSSchema('sbar')
        schema.manage_addField('id', 'CPS String Field') # same id
        schema.manage_addField('bar', 'CPS String Field') # kept
        schema.manage_addField('mail', 'CPS String Field') # renamed

        schema = stool.manage_addCPSSchema('smeta')
        schema.manage_addField('id', 'CPS String Field')
        schema.manage_addField('foo', 'CPS String Field')
        schema.manage_addField('bar', 'CPS String Field')
        schema.manage_addField('email', 'CPS String Field')

        dirfoo = self.pd.manage_addCPSDirectory('dirfoo',
                                                'CPS ZODB Directory')
        dirfoo.manage_changeProperties(schema='sfoo', id_field='idd')

        dirbar = self.pd.manage_addCPSDirectory('dirbar',
                                                'CPS ZODB Directory')
        dirbar.manage_changeProperties(schema='sbar', id_field='id')

        dirmeta = self.pd.manage_addCPSDirectory('dirmeta',
                                                 'CPS Meta Directory')
        dirmeta.manage_changeProperties(schema='smeta', id_field='id',
                                        title_field='bar')
        dirmeta.setBackingDirectories(
            ({'dir_id': 'dirfoo',
              'field_ignore': ('pasglop',),
              'missing_entry_expr': "python:{'foo': 'defaultfoo'}"
              },
             {'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, # back:meta
              },
             ))

        self.dirfoo = dirfoo
        self.dirbar = dirbar
        self.dirmeta = dirmeta


    def test_getEntry(self):
        id = 'LDHL'
        self.assertRaises(KeyError, self.dirmeta.getEntry, id)
        barentry = {'id': id, 'bar': 'brr', 'mail': 'ma'}
        okentry = {'id': id, 'foo': 'defaultfoo', 'bar': 'brr', 'email': 'ma'}
        self.dirbar.createEntry(barentry)
        entry = self.dirmeta.getEntry(id)
        self.assertEquals(entry, okentry)

    def test_listEntryIds(self):
        id = 'LDA'
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirbar.createEntry(barentry)
        id = 'LDB'
        fooentry = {'idd': id, 'foo': 'f', 'pasglop': 'p'}
        barentry = {'id': id, 'bar': 'b', 'mail': 'm'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        ids = self.dirmeta.listEntryIds()
        ids.sort()
        okids = ['LDA', 'LDB']
        self.assertEquals(okids, ids)

    def test_hasEntry(self):
        id = 'XOR'
        self.failIf(self.dirmeta.hasEntry(id))
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirbar.createEntry(barentry)
        self.assert_(self.dirmeta.hasEntry(id))

    def test_hasEntry_fail(self):
        id = 'BNE'
        self.failIf(self.dirmeta.hasEntry(id))
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        self.dirfoo.createEntry(fooentry)
        self.failIf(self.dirmeta.hasEntry(id))

    def test_deleteEntry(self):
        id = 'DJNZ'
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirmeta.hasEntry(id))
        barentry = {'id': id, 'bar': 'babar', 'mail': 'mymail@m'}
        self.dirbar.createEntry(barentry)
        self.assert_(self.dirmeta.hasEntry(id))
        self.dirmeta.deleteEntry(id)
        self.failIf(self.dirfoo.hasEntry(id))
        self.failIf(self.dirbar.hasEntry(id))
        self.failIf(self.dirmeta.hasEntry(id))

    def test_editEntry(self):
        # Build previous entry in backing dir
        id = 'BEQ'
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirbar.createEntry(barentry)
        # Now change it
        entry = {'id': id, 'bar': 'BAR', 'email': 'EMAIL@COM'}
        self.dirmeta.editEntry(entry)
        # Check changed
        okentry = {'id': id, 'foo': 'defaultfoo', 'bar': 'BAR',
                   'email': 'EMAIL@COM'}
        entry2 = self.dirmeta.getEntry(id)
        self.assertEquals(entry2, okentry)
        # Check backing dirs have changed
        fooentry2 = self.dirfoo.getEntry(id)
        barentry2 = self.dirbar.getEntry(id)
        fooentry3 = {'idd': id, 'foo': 'defaultfoo', 'pasglop': ''}
        barentry3 = {'id': id, 'bar': 'BAR', 'mail': 'EMAIL@COM'}
        self.assertEquals(fooentry2, fooentry3)
        self.assertEquals(barentry2, barentry3)

    def test_searchEntries_missing(self):
        dir = self.dirmeta
        fooentry1 = {'idd': 'DDD', 'foo': 'ouah', 'pasglop': 'arg'}
        barentry1 = {'id': 'DDD', 'bar': 'thebar', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry1)
        self.dirbar.createEntry(barentry1)
        barentry2 = {'id': 'EEE', 'bar': 'thebar', 'mail': 'ba@ba'}
        self.dirbar.createEntry(barentry2)

        ids = dir.searchEntries(bar='thebar')
        ids.sort()
        self.assertEquals(ids, ['DDD', 'EEE'])

        res = dir.searchEntries(bar='thebar', return_fields=['foo'])
        res.sort()
        self.assertEquals(res, [('DDD', {'foo': 'ouah'}),
                                ('EEE', {'foo': 'defaultfoo'})])

        res = dir.searchEntries(return_fields=['foo'])
        res.sort()
        self.assertEquals(res, [('DDD', {'foo': 'ouah'}),
                                ('EEE', {'foo': 'defaultfoo'})])

    # XXX must have test with a search on a field from a missing entry

    def XXXXXXXXXXXtest_searchEntries(self):
        # TODO FIXME: the code doesn't treat the case where we
        # do a search on an attribute that's in the missing entry.
        dir = self.dirmeta

        entry1 = {'id': 'AAA', 'foo': 'oof', 'bar': 'rab', 'email': 'lame@at'}
        dir.createEntry(entry1)
        entry2 = {'id': 'BBB', 'foo': 'oo', 'bar': 'man', 'email': 'evil@hell'}
        dir.createEntry(entry2)
        entry3 = {'id': 'CCC', 'foo': 'oo', 'bar': 'rab', 'email': 'yo@mama'}
        dir.createEntry(entry3)

        # Simple
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC'])

        ids = dir.searchEntries(id='AAA')
        self.assertEquals(ids, ['AAA'])
        ids = dir.searchEntries(foo='oo')
        ids.sort()
        self.assertEquals(ids, ['BBB', 'CCC'])
        ids = dir.searchEntries(bar='rab')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'CCC'])
        ids = dir.searchEntries(hooooole='ohle')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC'])
        ids = dir.searchEntries(email='evil@hell')
        self.assertEquals(ids, ['BBB'])

        # With field_ids
        res = dir.searchEntries(return_fields=['email'])
        res.sort()
        self.assertEquals(res, [('AAA', {'email': 'lame@at'}),
                                ('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'})])
        res = dir.searchEntries(foo='oo', return_fields=['email', 'pasglop'])
        res.sort()
        self.assertEquals(res, [('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'})])
        res = dir.searchEntries(email='lame@at', return_fields=['foo'])
        self.assertEquals(res, [('AAA', {'foo': 'oof'})])

        res = dir.searchEntries(foo='oof', return_fields=['id'])
        self.assertEquals(res, [('AAA', {'id': 'AAA'})])

        # Not strictly defined but test it anyway
        res = dir.searchEntries(return_fields=['blort'])
        res.sort()
        self.assertEquals(res, [('AAA', {}), ('BBB', {}), ('CCC', {})])
        res = dir.searchEntries(return_fields=['id'])
        res.sort()
        self.assertEquals(res, [('AAA', {'id':'AAA'}),
                                ('BBB', {'id':'BBB'}),
                                ('CCC', {'id':'CCC'})])

        # Fields coming from both dirs
        res = dir.searchEntries(foo='oo', return_fields=['email', 'foo'])
        res.sort()
        self.assertEquals(res, [('BBB', {'foo': 'oo', 'email': 'evil@hell'}),
                                ('CCC', {'foo': 'oo', 'email': 'yo@mama'})])

    def testBasicSecurity(self):
        self.assert_(self.dirmeta.isVisible())
        self.assert_(self.dirmeta.isCreateEntryAllowed())
        self.assert_(self.dirmeta.searchEntries() is not None)
        self.logout()
        self.assert_(not self.dirmeta.isVisible())
        self.assert_(not self.dirmeta.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dirmeta.searchEntries)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMetaDirectory))
    suite.addTest(unittest.makeSuite(TestMetaDirectoryMissing))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
