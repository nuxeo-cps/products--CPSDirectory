# TODO:
# - don't depend on getDocumentSchemas / getDocumentTypes but is there
#   an API for that ?

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from Testing import ZopeTestCase
from CPSDirectoryTestCase import CPSDirectoryTestCase
from AccessControl import Unauthorized

class TestZODBDirectory(CPSDirectoryTestCase):

    def makeDir(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('testzodb')
        schema.manage_addField('idd', 'CPS String Field')
        schema.manage_addField('foo', 'CPS String Field')
        schema.manage_addField('bar', 'CPS String List Field')

        dir = self.pd.manage_addCPSDirectory('zodbdir',
                                             'CPS ZODB Directory')
        dir.manage_changeProperties(schema='testzodb', id_field='idd')
        self.dir = dir

    def afterSetUp(self):
        self.login('manager')
        self.ws = self.portal.workspaces
        self.pd = self.portal.portal_directories
        self.makeDir()

    def beforeTearDown(self):
        self.logout()

    def testPresence(self):
        self.assertEquals(self.pd.zodbdir.meta_type, 'CPS ZODB Directory')

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())

    def testEmpty(self):
        dir = self.dir
        self.assertEqual(dir.listEntryIds(), [])

    def testCreation(self):
        dir = self.dir
        id = 'chien'
        entry = {'idd': id, 'foo': 'ouah', 'bar': ['4']}

        self.assertEqual(dir.listEntryIds(), [])
        self.assert_(not dir.hasEntry(id))
        self.assertRaises(KeyError, dir.getEntry, id)

        dir.createEntry(entry)
        self.assertRaises(KeyError, dir.createEntry, {'idd': id})

        self.assertEqual(dir.listEntryIds(), [id])
        self.assert_(dir.hasEntry(id))

        e = dir.getEntry(id)
        self.assertEquals(e, {'idd': id, 'foo': 'ouah', 'bar': ['4']})

        dir.deleteEntry(id)

        self.assertEqual(dir.listEntryIds(), [])
        self.assert_(not dir.hasEntry(id))
        self.assertRaises(KeyError, dir.getEntry, id)


    def testFetchWithComputedValues(self):
        dir = self.dir
        dir.title_field = 'baz'
        schema = self.portal.portal_schemas.testzodb
        schema.manage_addField('baz', 'CPS String Field',
                               read_ignore_storage=1,
                               read_process_expr='python: foo+"_yo"',
                               read_process_dependent_fields='foo',
                               )
        id = 'chien'
        entry = {'idd': id, 'foo': 'ouah', 'bar': ['4']}
        dir.createEntry(entry)

        e = dir.getEntry(id)
        ok = {'idd': id, 'foo': 'ouah', 'bar': ['4'], 'baz': 'ouah_yo'}
        self.assertEquals(e, ok)

        ids_titles = dir.listEntryIdsAndTitles()
        self.assertEquals(ids_titles, [(id, 'ouah_yo')])

    def testSearch(self):
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

        # Searches with return fields
        res = dir.searchEntries(foo='green', return_fields=['*'])
        self.assertEquals(res, [(id1, e1)])
        res = dir.searchEntries(foo='green', return_fields=['idd'])
        self.assertEquals(res, [(id1, {'idd': id1})])
        res = dir.searchEntries(foo='green', return_fields=['foo'])
        self.assertEquals(res, [(id1, {'foo': foo1})])
        res = dir.searchEntries(foo='green', return_fields=['foo', 'idd'])
        self.assertEquals(res, [(id1, {'idd': id1, 'foo': foo1})])
        res = dir.searchEntries(foo='green', return_fields=['foo', 'bar'])
        self.assertEquals(res, [(id1, {'foo': foo1, 'bar': bar1})])
        res = dir.searchEntries(foo='green', return_fields=['zblurg'])
        self.assertEquals(res, [(id1, {})])


    def testSearchSubstrings(self):
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

class TestDirectoryEntryLocalRoles(CPSDirectoryTestCase):
    # We test entry local roles on ZODB directory as this is the
    # simplest form of directory with minimal dependencies.

    def makeDir(self):
        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('testzodb')
        schema.manage_addField('id', 'CPS String Field')
        schema.manage_addField('name', 'CPS String Field')

        dir = self.pd.manage_addCPSDirectory('zodbdir',
                                             'CPS ZODB Directory')
        dir.manage_changeProperties(
            schema='testzodb',
            id_field='id',
            acl_directory_view_roles='BigSmurf',
            acl_entry_create_roles='BigSmurf; DoAlbator',
            acl_entry_delete_roles='BigSmurf; DoChapi',
            acl_entry_view_roles='BigSmurf; DoPeter',
            acl_entry_edit_roles='BigSmurf; DoPeter',
            )
        self.dir = dir

        res = dir.addEntryLocalRole('BigSmurf', 'python:user_id == "manager"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoAlbator', 'python:id == "albator"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoChapi', 'python:name == "ChapiChapo"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoPeter', 'python:name == "Peterpan"')
        self.assertEquals(res, '')

        e = {'id': 'peterpan', 'name': 'Peterpan'}
        dir.createEntry(e)

    def afterSetUp(self):
        self.login('manager')
        self.ws = self.portal.workspaces
        self.pd = self.portal.portal_directories
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
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dir.searchEntries)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZODBDirectory))
    suite.addTest(unittest.makeSuite(TestDirectoryEntryLocalRoles))
    return suite

if __name__ == '__main__':
    TestRunner().run(test_suite())
