# -*- encoding: iso-8859-15 -*-
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

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import Unauthorized
from OFS.Folder import Folder
from DateTime import DateTime

from Products.StandardCacheManagers.RAMCacheManager import RAMCacheManager

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeUserFolder
from Products.CPSDirectory.tests.fakeCps import FakeRoot

class TestZODBDirectory(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = FakeDirectoryTool()
        self.root.portal.acl_users = FakeUserFolder()
        self.portal = self.root.portal
        self.pd = self.portal.portal_directories

    def makeSchema(self):
        stool = self.portal.portal_schemas
        s = FakeSchema({
            'idd': FakeField(),
            'foo': FakeField(),
            'bar': FakeField(),
            })
        stool._setObject('testzodb', s)

    def makeDir(self):
        from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
        dtool = self.portal.portal_directories
        zdir = ZODBDirectory('zodbdir',
                           id_field='idd',
                           title_field='foo',
                           schema='testzodb',
                           schema_search='',
                           layout='',
                           layout_search='',
                           password_field='',
                           acl_directory_view_roles='test_role_1_',
                           acl_entry_create_roles='test_role_1_',
                           acl_entry_delete_roles='test_role_1_',
                           acl_entry_view_roles='test_role_1_',
                           acl_entry_edit_roles='test_role_1_',
                           )
        dtool._setObject(zdir.getId(), zdir)
        self.dir = dtool.zodbdir

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

    def testPresence(self):
        self.assertEquals(self.pd.zodbdir.meta_type, 'CPS ZODB Directory')

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())

    def testEmpty(self):
        zdir = self.dir
        self.assertEqual(zdir.listEntryIds(), [])

    def testCreation(self):
        zdir = self.dir
        id = 'chien'
        entry = {'idd': id, 'foo': 'ouah', 'bar': ['4']}

        self.assertEqual(zdir.listEntryIds(), [])
        self.assert_(not zdir.hasEntry(id))
        self.assertRaises(KeyError, zdir.getEntry, id)

        zdir.createEntry(entry)
        self.assertRaises(KeyError, zdir.createEntry, {'idd': id})

        self.assertEqual(zdir.listEntryIds(), [id])
        self.assertEqual(zdir.listEntryIdsAndTitles(), [(id, 'ouah')])
        self.assert_(zdir.hasEntry(id))

        e = zdir.getEntry(id)
        self.assertEquals(e, {'idd': id, 'foo': 'ouah', 'bar': ['4']})

        zdir.deleteEntry(id)

        self.assertEqual(zdir.listEntryIds(), [])
        self.assertEqual(zdir.listEntryIdsAndTitles(), [])
        self.assert_(not zdir.hasEntry(id))
        self.assertRaises(KeyError, zdir.getEntry, id)

    def test__getEntry(self):
        # this actually tests code from BaseDirectory

        # preparation
        zdir = self.dir
        id = 'chien'
        entry = {'idd': id, 'foo': 'ouah', 'bar': ['4']}
        zdir.createEntry(entry)

        # forbid side effects
        self.assertEquals(zdir.listEntryIds(), [id])

        # assertions
        self.assertEquals(zdir._getEntry(id), entry)
        self.assertEquals(zdir._getEntry('abc', default=2), 2)
        self.assertRaises(KeyError, zdir._getEntry, 'abc')

    def testSearch(self):
        zdir = self.dir

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'idd': id1, 'foo': foo1, 'bar': bar1}
        zdir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'idd': id2, 'foo': foo2, 'bar': bar2}
        zdir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### With substrings
        zdir.search_substring_fields = ['idd']

        # search that was possible on members/groups/roles
        # directories and should be made on ZODB directories now that they are
        # the default CPS directories (?)
        res = zdir.searchEntries(idd='*')
        self.assertEquals(res, ids)

        ### Without substrings
        zdir.search_substring_fields = []

        # Basic searches
        res = zdir.searchEntries(idd=id1)
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(idd=[id1])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=foo1)
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=[foo1])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar='a123')
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar=['a123'])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [id1])

        # search on inexistent keys should not return all entries
        res = zdir.searchEntries(blurp='haha')
        # FIXME
        #self.assertEquals(res, [])

        # empty searches should not return anything
        res = zdir.searchEntries(return_fields=['id'])
        # FIXME, bug exists when return fields are provided (searchEntries()
        # does not return anything)
        #
        # XXX DIV: protection against empty searches was implemented at the
        # zpt level, so this test is not needed anymore, right?
        #self.assertEquals(res, [])

        # Multi-field searches
        res = zdir.searchEntries(idd=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [id2])
        res = zdir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [id1])

        # no search_substring_fields are set: no results
        res = zdir.searchEntries(idd='re')
        self.assertEquals(res, [])
        res = zdir.searchEntries(idd='tre')
        self.assertEquals(res, [])
        res = zdir.searchEntries(idd='TREE')
        self.assertEquals(res, [])
        res = zdir.searchEntries(foo='e')
        self.assertEquals(res, [])
        res = zdir.searchEntries(bar='812a')
        self.assertEquals(res, [])
        res = zdir.searchEntries(bar='gr')
        self.assertEquals(res, [])
        res = zdir.searchEntries(bar=['gr'])
        self.assertEquals(res, [])
        res = zdir.searchEntries(foo='E', bar='12')
        self.assertEquals(res, [])

        # Searches with return fields
        res = zdir.searchEntries(foo='green', return_fields=['*'])
        self.assertEquals(res, [(id1, e1)])
        res = zdir.searchEntries(foo='green', return_fields=['idd'])
        self.assertEquals(res, [(id1, {'idd': id1})])
        res = zdir.searchEntries(foo='green', return_fields=['foo'])
        self.assertEquals(res, [(id1, {'foo': foo1})])
        res = zdir.searchEntries(foo='green', return_fields=['foo', 'idd'])
        self.assertEquals(res, [(id1, {'idd': id1, 'foo': foo1})])
        res = zdir.searchEntries(foo='green', return_fields=['foo', 'bar'])
        self.assertEquals(res, [(id1, {'foo': foo1, 'bar': bar1})])
        res = zdir.searchEntries(foo='green', return_fields=['zblurg'])
        self.assertEquals(res, [(id1, {})])

        # typed searches
        zdir.editEntry({'idd': id1, 'foo': True})
        zdir.editEntry({'idd': id2, 'foo': False})
        res = zdir.searchEntries(foo=False)
        self.assertEquals(res, [id2])

        # typed searches with DateTime
        zdir.editEntry({'idd':id1, 'foo':DateTime('2000/01/01')})
        zdir.editEntry({'idd':id2, 'foo':DateTime('2000/02/02')})
        res = zdir.searchEntries(foo=DateTime('2000/01/01'))
        self.assertEquals(res, [id1])

    def test_renderCsvSearch(self):
        # this actually tests code from BaseDirectory

        # preparation
        zdir = self.dir
        zdir.createEntry({'idd': 'chien', 'foo': 'ouah', 'bar': 'poil'})
        zdir.createEntry({'idd': 'canard', 'foo': 'coin', 'bar': 'plume'})
        zdir.createEntry({'idd': 'cobra', 'foo': 'ssss', 'bar': u'\xe9caille'})

        # forbid side effects
        self.assertEquals(len(zdir.listEntryIds()), 3)

        return_fields = (
                         ('idd', 'Animal'),
                         ('foo', 'Cri'),
                         ('bar', 'Surface')
                         )

        self.assertEquals("Animal,Cri,Surface\r\n"
                          "chien,ouah,poil\r\n",
                          zdir.csvExport(foo='ouah', output_charset='latin1',
                                         return_fields=return_fields))

        #Reproducing ticket #2523
        unicode_return_fields2 = (
                                ('idd',u'qw\xe8'),
                                ('foo', 'Cri'),
                                ('bar', 'Surface')
                                )

        self.assertEquals('qw\xe8,Cri,Surface\r\n'
                           'chien,ouah,poil\r\n',
                           zdir.csvExport(foo='ouah',output_charset='latin1',
                           return_fields = unicode_return_fields2)
                           )

        zdir.search_substring_fields = ['bar']
        result = zdir.csvExport(bar='p', 
                                return_fields=return_fields).split('\r\n')
        result.sort()
        
        expected = ["Animal,Cri,Surface", 
                    "chien,ouah,poil",
                    "canard,coin,plume", ""]
        expected.sort()
        self.assertEquals(result, expected)
        
        self.assertEquals("Cri,Surface\r\n"
                          "ssss,\xe9caille\r\n",
                          zdir.csvExport(idd='cobra', output_charset='latin1',
                                         return_fields=return_fields[1:]))

        self.assertEquals("Cri,Surface\r\n"
                          "ssss,\xc3\xa9caille\r\n",
                          zdir.csvExport(idd='cobra', 
                                         output_charset='utf-8',
                                         return_fields=return_fields[1:]))

        # now with booleans (cheating a lot with schema)
        zdir.createEntry({'idd': 'mute', 'foo': False, 'bar': 'plume'})
        self.assertEquals("Cri,Surface\r\n"
                          "False,plume\r\n",
                          zdir.csvExport(idd='mute',
                                         output_charset='utf-8',
                                         return_fields=return_fields[1:]))

        # minimal field security check and resilience
        from Products.CPSSchemas.DataModel import ReadAccessError
        def checkReadAccess(*args):
            raise ReadAccessError("You kidding ?")
        idd_field = self.portal.portal_schemas.testzodb['foo']
        idd_field.checkReadAccess = checkReadAccess
        self.assertEquals("Animal,Cri,Surface\r\n"

                          "cobra,,\xe9caille\r\n",
                          zdir.csvExport(idd='cobra', output_charset='latin1',
                                         return_fields=return_fields))



    def testCache(self):
        zdir = self.dir
        dtool = self.portal.portal_directories

        # REQUEST is necessary for ZCacheable methods.
        # Note that these swallow AttributeErrors, making them look as a
        # cache misses
        zdir.REQUEST = self.app.REQUEST

        man_id = 'cache_manager'
        dtool._setObject(man_id, RAMCacheManager(man_id))
        dtool.REQUEST = self.app.REQUEST
        getCacheReport = dtool.cache_manager.getCacheReport
        zdir.ZCacheable_setManagerId(man_id)
        self.assert_(zdir.ZCacheable_isCachingEnabled())
        self.assertEquals(zdir.ZCacheable_getManager(), dtool[man_id])

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'idd': id1, 'foo': foo1, 'bar': bar1}
        zdir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'idd': id2, 'foo': foo2, 'bar': bar2}
        zdir.createEntry(e2)

        # cache not used yet
        self.assertEquals(getCacheReport(), [])

        # filling the cache
        res = zdir.searchEntries(idd=id1)
        self.assertEquals(res, [id1])

        # check cache is filled
        self.assertEquals(len(getCacheReport()), 1)
        self.assertEquals(getCacheReport()[0]['entries'], 1)
        self.assertEquals(getCacheReport()[0]['hits'], 0)

        # check initial result not incorrectly mutable in cache
        res.append('babar')
        res2 = zdir.searchEntries(idd=id1)
        self.assertEquals(res2, [id1])

        # check cached result not incorrectly mutable
        res.append('bibi')
        res2 = zdir.searchEntries(idd=id1)
        self.assertEquals(res2, [id1])

        # check cache is used
        self.assertEquals(getCacheReport()[0]['entries'], 1)
        self.assertEquals(getCacheReport()[0]['hits'], 2)

        # avoiding worst side-effects
        self.assertEquals(zdir.searchEntries(idd=id2), [id2])

        # check cache is filled
        self.assertEquals(len(getCacheReport()), 1)
        self.assertEquals(getCacheReport()[0]['entries'], 2)

        # return_fields is part of the keys:
        res = zdir.searchEntries(idd=id1, return_fields=['foo'])
        self.assertEquals(res, [(id1, {'foo': foo1})])

        # check not incorrectly mutable
        res.append('babar')
        res[0][1]['zap'] = 'zip'
        res2 = zdir.searchEntries(idd=id1, return_fields=['foo'])
        self.assertEquals(res2, [(id1, {'foo': foo1})])

        # editing entries clears the cache
        e2['foo'] = 'foo_new'
        zdir.editEntry(e2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(idd=id1), [id1])
        self.assertEquals(len(getCacheReport()), 1)

        # deleting entry clears the cache
        zdir.deleteEntry(id2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(idd=id1), [id1])
        self.assertEquals(len(getCacheReport()), 1)

        # adding entries clears the cache
        zdir.createEntry(e2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(idd=id1), [id1])
        self.assertEquals(len(getCacheReport()), 1)

    def testSearchSubstrings(self):
        zdir = self.dir

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        e1 = {'idd': id1, 'foo': foo1, 'bar': bar1}
        zdir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        e2 = {'idd': id2, 'foo': foo2, 'bar': bar2}
        zdir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### With substrings
        zdir.search_substring_fields = ['foo', 'bar']

        # Basic searches
        res = zdir.searchEntries(idd=id1)
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(idd=[id1])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=foo1)
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=[foo1])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar='a123')
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar=['a123'])
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [id1])

        # Multi-field searches
        res = zdir.searchEntries(idd=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [id1])
        res = zdir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [id2])
        res = zdir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [id1])

        # Substring searches
        res = zdir.searchEntries(idd='re')
        self.assertEquals(res, [])
        res = zdir.searchEntries(idd='TREE')
        self.assertEquals(res, [])
        res = zdir.searchEntries(foo='e')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar='812a')
        self.assertEquals(res, [id2])
        res = zdir.searchEntries(bar='gr')
        self.assertEquals(res, ids)
        res = zdir.searchEntries(bar=['gr'])
        self.assertEquals(res, [])
        res = zdir.searchEntries(foo='E', bar='12')
        self.assertEquals(res, ids)

class TestDirectoryEntryLocalRoles(ZopeTestCase):
    # We test entry local roles on ZODB directory as this is the
    # simplest form of directory with minimal dependencies.

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

    def makeSchema(self):
        stool = self.portal.portal_schemas
        s = FakeSchema({
            'id': FakeField(),
            'name': FakeField(),
            })
        stool._setObject('testzodb', s)

    def makeDir(self):
        from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
        dtool = self.portal.portal_directories
        zdir = ZODBDirectory('members',
                           id_field='id',
                           title_field='name',
                           schema='testzodb',
                           schema_search='',
                           layout='',
                           layout_search='',
                           password_field='',
                           acl_directory_view_roles='BigSmurf',
                           acl_entry_create_roles='BigSmurf; DoAlbator',
                           acl_entry_delete_roles='BigSmurf; DoChapi',
                           acl_entry_view_roles='BigSmurf; DoPeter',
                           acl_entry_edit_roles='BigSmurf; DoPeter',
                           )
        dtool._setObject(zdir.getId(), zdir)
        self.dir = dtool.members

        res = zdir.addEntryLocalRole('BigSmurf', 'python:user_id == "test_user_1_"')
        self.assertEquals(res, '')
        res = zdir.addEntryLocalRole('DoAlbator', 'python:id == "albator"')
        self.assertEquals(res, '')
        res = zdir.addEntryLocalRole('DoChapi', 'python:name == "ChapiChapo"')
        self.assertEquals(res, '')
        res = zdir.addEntryLocalRole('DoPeter', 'python:name == "Peterpan"')
        self.assertEquals(res, '')

        e = {'id': 'peterpan', 'name': 'Peterpan'}
        self.dir.createEntry(e)

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.login('test_user_1_')
        self.makeSite()
        self.makeSchema()
        self.makeDir()

    def beforeTearDown(self):
        self.logout()

    def testDirectoryView(self):
        meth = self.dir.isVisible
        self.assert_(meth())
        self.logout()
        self.assert_(not meth())

    def testCreateEntry(self):
        meth = self.dir.isCreateEntryAllowed
        self.assert_(meth())
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(id='brr'))
        self.assert_(meth(id='albator'))
        self.assert_(meth(entry={'id': 'albator', 'name': 'daffy'}))

    def testDeleteEntry(self):
        meth = self.dir.isDeleteEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='peterpan'))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(id='peterpan'))
        self.assert_(meth(entry={'id': 'bzzzz', 'name': 'ChapiChapo'}))

    def testViewEntry(self):
        meth = self.dir.isViewEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='peterpan'))
        self.assert_(meth(entry={'name': 'Peterpan'}))
        self.assert_(meth(entry={'name': 'Blurp'}))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(entry={'name': 'Blurp'}))
        self.assert_(meth(id='peterpan'))
        self.assert_(meth(entry={'name': 'Peterpan'}))

    def testEditEntry(self):
        meth = self.dir.isEditEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='peterpan'))
        self.assert_(meth(entry={'name': 'Peterpan'}))
        self.assert_(meth(entry={'name': 'Blurp'}))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(entry={'name': 'Blurp'}))
        self.assert_(meth(id='peterpan'))
        self.assert_(meth(entry={'name': 'Peterpan'}))
        # readonly behavior
        self.dir.readonly = True
        self.dir._editEntry({'name': 'Peterspoon', 'id': 'peterpan'})
        self.assertEquals(self.dir._getEntry('peterpan')['name'],
                          'Peterpan')

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        e = {'id': 'albator', 'name': 'Albator'}
        self.dir.createEntry(e)
        self.assert_(self.dir.searchEntries() is not None)
        self.assertEquals(self.dir.getEntry('albator'), {'id': 'albator',
                                                          'name': 'Albator'})
        self.assertEquals(self.dir.getEntry('peterpan'), {'id': 'peterpan',
                                                          'name': 'Peterpan'})
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dir.searchEntries)
        self.assertRaises(Unauthorized, self.dir.getEntry, 'albator')
        self.assertEquals(self.dir.getEntry('albator', default=None), None)

        # Because of the entry local role we still have the right to view
        # PeterPan :
        self.assertEquals(self.dir.getEntry('peterpan'), {'id': 'peterpan',
                                                          'name': 'Peterpan'})


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZODBDirectory))
    suite.addTest(unittest.makeSuite(TestDirectoryEntryLocalRoles))
    return suite

