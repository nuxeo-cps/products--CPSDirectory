import os, sys

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import Unauthorized
from OFS.Folder import Folder

from Products.StandardCacheManagers.RAMCacheManager import RAMCacheManager

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot


class TestZODBDirectory(ZopeTestCase):

    def makeSite(self):
        self.root = FakeRoot()
        self.root.portal = Folder('portal')
        self.root.portal.portal_schemas = FakeSchemasTool()
        self.root.portal.portal_directories = FakeDirectoryTool()
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

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        self.assert_(self.dir.searchEntries() is not None)
        self.assertEquals(self.dir.getEntry('peterpan'), {'id': 'peterpan',
                                                          'name': 'Peterpan'})
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dir.searchEntries)
        self.assertRaises(Unauthorized, self.dir.getEntry, 'peterpan')
        self.assertEquals(self.dir.getEntry('peterpan', default=None), None)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZODBDirectory))
    suite.addTest(unittest.makeSuite(TestDirectoryEntryLocalRoles))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
