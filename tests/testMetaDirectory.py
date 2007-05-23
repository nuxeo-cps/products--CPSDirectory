# (C) Copyright 2004-2007 Nuxeo SAS <http://nuxeo.com>
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
from Products.CPSDirectory.tests.fakeCps import FakeUserFolder
from Products.CPSDirectory.tests.fakeCps import FakeRoot

from Products.CPSDirectory.ZODBDirectory import ZODBDirectory

class LoggerZODBDirectory(ZODBDirectory):
    def _searchEntries(self, *args, **kwargs):
        self.tests_called_search = True
        return ZODBDirectory._searchEntries(self, *args, **kwargs)


class TestMetaDirectory(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        utool = Folder('portal_url')
        utool.getPortalObject = lambda : self.root.portal
        self.root.portal.portal_url = utool
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = FakeDirectoryTool()
        self.root.portal.acl_users = FakeUserFolder()
        self.portal = self.root.portal
        self.pd = self.portal.portal_directories

    def makeSchemas(self):
        stool = self.portal.portal_schemas
        s = FakeSchema({
            'idd': FakeField(),
            'foo': FakeField(),
            'pasglop': FakeField(),
            })
        stool._setObject('sfoo', s)
        s = FakeSchema({
            'id': FakeField(),
            'bar': FakeField(),
            'mail': FakeField(),
            })
        stool._setObject('sbar', s)
        s = FakeSchema({
            'id': FakeField(),
            'foo': FakeField(),
            'bar': FakeField(),
            'email': FakeField(),
            })
        stool._setObject('smeta', s)

    def makeDirs(self):
        from Products.CPSDirectory.MetaDirectory import MetaDirectory

        dtool = self.portal.portal_directories
        dirfoo = ZODBDirectory('dirfoo', schema='sfoo', id_field='idd',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirfoo.getId(), dirfoo)

        dirbar = LoggerZODBDirectory('dirbar', schema='sbar', id_field='id',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirbar.getId(), dirbar)

        dirmeta = MetaDirectory('dirmeta', schema='smeta', id_field='id',
                title_field='bar',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirmeta.getId(), dirmeta)

        dtool.dirmeta.setBackingDirectories(
            ({'dir_id': 'dirfoo',
              'field_ignore': ('pasglop',),
              },
             {'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, # convention is back:meta
                 },
             ))

        self.dirfoo = dtool.dirfoo
        self.dirbar = dtool.dirbar
        self.dirmeta = dtool.dirmeta

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchemas()
        self.makeDirs()

class TestMetaDirectoryNoMissing(TestMetaDirectory):

    def test_properties(self):
        props = self.dirmeta.propertyIds()
        self.assert_(props)
        self.failIf('search_substring_fields' in props)

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

    def test_searchEntries_renames_1266(self):
        # use-case of bug #1266: renames couldn't work in _searchEntries
        # for two dirs at once
        dir = self.dirmeta
        dir.setBackingDirectories(
            ({'dir_id': 'dirfoo',
              'field_rename': {'pasglop': 'glop',}, # convention is back:meta
              },
             {'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, 
                 },
             ))

        fooentry = {'idd': 'DDD', 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': 'DDD', 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        res = dir.searchEntries(id='DDD', return_fields=['glop', 'email', ])
        self.assertEquals(res, [('DDD', {'glop' : 'arg', 'email': 'me@here'})])
        
    def test_searchEntries_renames_notinj(self):
        # two different ids in the meta but same field ids in backings
        # XXX an entire test case for this setting would be more appropriate

        dtool = self.portal.portal_directories
        stool = self.portal.portal_schemas

        # we need a new backing        
        from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
        from Products.CPSDirectory.MetaDirectory import MetaDirectory
        dirbabar = ZODBDirectory('dirbabar', schema='sbar', id_field='id',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirbabar.getId(), dirbabar)
        self.dirbabar = dtool.dirbabar

        s = FakeSchema({
            'id': FakeField(),
            'foo': FakeField(),
            'bar': FakeField(),
            'email': FakeField(),
            'email_babar' : FakeField(),
            })
        stool._setObject('smeta_babar', s)

        dirmeta_babar = MetaDirectory('dirmeta_babar',
                                     schema='smeta_babar', id_field='id',
                title_field='bar',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirmeta_babar.getId(), dirmeta_babar)

        dir = dtool.dirmeta_babar
        dir.setBackingDirectories( 
            ({'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, # convention is back:meta
                 },
             {'dir_id': 'dirbabar',
              'field_rename': {'mail': 'email_babar'}, 
                 },
             ))

        barentry = {'id': 'DDD', 'bar': 'brr', 'mail': 'me@here'}
        babarentry = {'id': 'DDD', 'bar': 'sss', 'mail': 'babar@here'}
        self.dirbar.createEntry(barentry)
        self.dirbabar.createEntry(babarentry)
        res = dir.searchEntries(id='DDD',
                                return_fields=['email', 'email_babar'])
        self.assertEquals(res, [('DDD', {'email_babar' : 'babar@here',
                                         'email': 'me@here'})])

    def testSearchSubstrings(self):
        # most of this test is a copy/paste from the one in ZODB Directory
        dir = self.dirmeta

        ### allow substrings in backings
        self.dirbar.search_substring_fields = ['bar']
        self.dirfoo.search_substring_fields = ['foo']

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'id': id1, 'foo': foo1, 'bar': bar1}
        dir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'id': id2, 'foo': foo2, 'bar': bar2}
        dir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        # Basic searches
        res = dir.searchEntries(id=id1)
        self.assertEquals(res, [id1])
        res = dir.searchEntries(id=[id1])
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
        res = dir.searchEntries(id=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [id1])
        res = dir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [id2])
        res = dir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [id1])

        # Substring searches
        res = dir.searchEntries(id='re')
        self.assertEquals(res, [])
        res = dir.searchEntries(id='TREE')
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

        # typed searches
        dir.editEntry({'id': id1, 'foo': True})
        dir.editEntry({'id': id2, 'foo': False})
        res = dir.searchEntries(foo=False)
        self.assertEquals(res, [id2])

class TestMetaDirectoryMissing(TestMetaDirectory):

    def afterSetUp(self):
        TestMetaDirectory.afterSetUp(self)
        self.dirmeta.setBackingDirectories(
            ({'dir_id': 'dirfoo',
              'field_ignore': ('pasglop',),
              'missing_entry_expr': "python:{'foo': 'defaultfoo'}"
              },
             {'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, # back:meta
              },
             ))

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
        # Check changed (Missing entry takes precedence over field's default).
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

    def test_searchEntries(self):
        dir = self.dirmeta

        entry1 = {'id': 'AAA', 'foo': 'oof', 'bar': 'rab', 'email': 'lame@at'}
        dir.createEntry(entry1)
        entry2 = {'id': 'BBB', 'foo': 'oo', 'bar': 'man', 'email': 'evil@hell'}
        dir.createEntry(entry2)
        entry3 = {'id': 'CCC', 'foo': 'oo', 'bar': 'rab', 'email': 'yo@mama'}
        dir.createEntry(entry3)
        barentry = {'id': 'DDD', 'bar': 'baronly', 'mail' : 'brian@spam'}
        self.dirbar.createEntry(barentry)
        self.failIf(self.dirfoo._hasEntry('DDD'))

        # Simple
        ids = dir.searchEntries()
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC', 'DDD'])

        ids = dir.searchEntries(id='AAA')
        self.assertEquals(ids, ['AAA'])
        
        ids = dir.searchEntries(foo='oo')
        ids.sort()
        self.assertEquals(ids, ['BBB', 'CCC'])

        ids = dir.searchEntries(bar='baronly', foo='defaultfoo')
        ids.sort()
        self.assertEquals(ids, ['DDD'])
        
        # used to produce empty search in dirbar. Since query cannot match
        # dirfoo's missing entry. search in dirbar shouldn't be done at all
        # (see https://svn.nuxeo.org/trac/pub/ticket/995)
        self.dirbar.tests_called_search = False
        ids = dir.searchEntries(foo='oo')
        ids.sort()
        self.assertEquals(ids, ['BBB', 'CCC'])
        self.failIf(self.dirbar.tests_called_search)
        self.dirbar.tests_called_search = True
        
        ids = dir.searchEntries(foo='oo')
        ids.sort()
        self.assertEquals(ids, ['BBB', 'CCC'])
        
        ids = dir.searchEntries(bar='rab')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'CCC'])
        
        # unknown field: equivalent to an empty search
        ids = dir.searchEntries(hooooole='ohle')
        ids.sort()
        self.assertEquals(ids, ['AAA', 'BBB', 'CCC', 'DDD'])
        
        ids = dir.searchEntries(email='evil@hell')
        self.assertEquals(ids, ['BBB'])

        # With field_ids
        res = dir.searchEntries(return_fields=['email'])
        res.sort()
        self.assertEquals(res, [('AAA', {'email': 'lame@at'}),
                                ('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'}),
                                ('DDD', {'email': 'brian@spam'}),
                                ])

        res = dir.searchEntries(foo='oo', return_fields=['email', 'pasglop'])
        res.sort()
        self.assertEquals(res, [('BBB', {'email': 'evil@hell'}),
                                ('CCC', {'email': 'yo@mama'})])

        res = dir.searchEntries(email='lame@at', return_fields=['foo'])
        self.assertEquals(res, [('AAA', {'foo': 'oof'})])

        res = dir.searchEntries(email='brian@spam', return_fields=['foo'])
        self.assertEquals(res, [('DDD', {'foo': 'defaultfoo'})])

        res = dir.searchEntries(foo='oof', return_fields=['id'])
        self.assertEquals(res, [('AAA', {'id': 'AAA'})])

        # Not strictly defined but test it anyway
        res = dir.searchEntries(return_fields=['blort'])
        res.sort()
        self.assertEquals(res, [('AAA', {}), ('BBB', {}),
                                ('CCC', {}),('DDD', {}),
                                ])

        res = dir.searchEntries(return_fields=['id'])
        res.sort()

        self.assertEquals(res, [('AAA', {'id':'AAA'}),
                                ('BBB', {'id':'BBB'}),
                                ('CCC', {'id':'CCC'}),
                                ('DDD', {'id':'DDD'})
                                ])

        # Fields coming from both dirs
        res = dir.searchEntries(foo='oo', return_fields=['email', 'foo'])
        res.sort()
        self.assertEquals(res, [('BBB', {'foo': 'oo', 'email': 'evil@hell'}),
                                ('CCC', {'foo': 'oo', 'email': 'yo@mama'})])

        res = dir.searchEntries(foo='defaultfoo',
                                return_fields=['email', 'foo'])
        res.sort()
        self.assertEquals(res, [('DDD', {'foo': 'defaultfoo',
                                         'email': 'brian@spam'}),
                                ])

        # Substring on the missing
        self.dirfoo.search_substring_fields = ['foo']
        res = dir.searchEntries(bar='baronly', foo='default',
                                return_fields=['foo']) 
        res.sort()
        self.assertEquals(res, [('DDD', {'foo': 'defaultfoo'})])

    def testBasicSecurity(self):
        self.assert_(self.dirmeta.isVisible())
        self.assert_(self.dirmeta.isCreateEntryAllowed())
        self.assert_(self.dirmeta.searchEntries() is not None)
        self.logout()
        self.assert_(not self.dirmeta.isVisible())
        self.assert_(not self.dirmeta.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dirmeta.searchEntries)

class TestMetaStackingDirectory(TestMetaDirectory):
    #GR: I actually saw a case where a problem was specific
    #to the situation where a stacking is behind a meta

    def makeDirs(self):
        TestMetaDirectory.makeDirs(self)
        from Products.CPSDirectory.StackingDirectory import StackingDirectory

        # now replace 'dirfoo' with a stacking with two backings:
        #  - original 'dirfoo'
        #  - 'dirfoo_foo': same as dirfoo with id_field: foo

        dtool = self.portal.portal_directories

        dirfoo = LoggerZODBDirectory('dirfoo_foo', id_field='foo',
                                     schema='sfoo',
                acl_directory_view_roles='test_role_1_',
                acl_entry_create_roles='test_role_1_',
                acl_entry_delete_roles='test_role_1_',
                acl_entry_view_roles='test_role_1_',
                acl_entry_edit_roles='test_role_1_',
                )
        dtool._setObject(dirfoo.getId(), dirfoo)
        self.dirfoo_foo = dtool.dirfoo_foo

        dirsfoo = StackingDirectory('dirsfoo', schema='sfoo', id_field='idd',
                                    backing_dirs=('dirfoo', 'dirfoo_foo'),
                                    creation_dir='dirfoo',
                                    acl_directory_view_roles='test_role_1_',
                                    acl_entry_create_roles='test_role_1_',
                                    acl_entry_delete_roles='test_role_1_',
                                    acl_entry_view_roles='test_role_1_',
                                    acl_entry_edit_roles='test_role_1_',
                                    )
        dtool._setObject(dirsfoo.getId(), dirsfoo)

        self.dirmeta.setBackingDirectories(
            ({'dir_id': 'dirsfoo',},
             {'dir_id': 'dirbar',
              'field_rename': {'mail': 'email'}, # convention is back:meta
                 },
             ))
        self.dirfoo = dtool.dirsfoo

    def makeSchemas(self):
        TestMetaDirectory.makeSchemas(self)
        # add 'pasglop' to 'smeta' schema
        stool = self.portal.portal_schemas
        s = FakeSchema({
            'id': FakeField(),
            'foo': FakeField(),
            'bar': FakeField(),
            'email': FakeField(),
            'pasglop': FakeField(),
            })
        stool.manage_delObjects(['smeta'])
        stool._setObject('smeta', s)

    def test_editEntry(self):
        #this test breaks if BaseStorageAdapter.getMandatoryFieldIds
        #returns ()

        # backing of stacking with same id field
        id = '111'
        fooentry = {'idd': id, 'foo': 'ouah', 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'brr', 'mail': 'me@here'}
        self.dirfoo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)

        self.dirmeta.editEntry({'id': id, 'pasglop': 'glop'})
        self.assertEquals(self.dirmeta.getEntry(id)['pasglop'], 'glop')

        # backing of stacking with different id field
        id = '222'
        fooentry = {'idd':  id, 'foo': "foo id", 'pasglop': 'arg'}
        barentry = {'id': id, 'bar': 'bra', 'mail': 'she@here'}
        self.dirfoo_foo.createEntry(fooentry)
        self.dirbar.createEntry(barentry)
        self.assertEquals(self.dirfoo.getEntry(id), fooentry)

        self.dirmeta.editEntry({'id': id, 'pasglop': 'glop'})
        self.assertEquals(self.dirmeta.getEntry(id)['pasglop'], 'glop')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMetaDirectoryNoMissing))
    suite.addTest(unittest.makeSuite(TestMetaDirectoryMissing))
    suite.addTest(unittest.makeSuite(TestMetaStackingDirectory))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
