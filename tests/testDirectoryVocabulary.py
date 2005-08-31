# TODO: check that "hack" in __getitem__ for dealing with dependency
# between fields is ok

import os, sys

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from OFS.Folder import Folder

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot
from Products.CPSDirectory.DirectoryVocabulary import DirectoryVocabulary


class TestDirectoryVocabulary(ZopeTestCase):

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
        dir = ZODBDirectory('zodbdir',
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
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.zodbdir

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()
        dvoc  = DirectoryVocabulary('test_dvoc')
        dvoc._getDirectory = lambda: self.dir
        dvoc.empty_key_value = 'empty'
        dvoc.empty_key_pos = 'first'
        self.dvoc = dvoc
        data = {
            'toto1': 'toto1_val',
            'toto2': 'toto2_val',
            'toto3': 'toto3_val',
            }
        for k, v in data.items():
            self.dir.createEntry({'idd': k, 'foo': v})
        self.data = data

    def test__getitem__(self):
        dvoc = self.dvoc
        for k, v in self.data.items():
            self.assertEquals(dvoc[k], v)
        self.assertRaises(KeyError, lambda: dvoc['NotExisting'])

    def test_get(self):
        dvoc = self.dvoc
        for k, v in self.data.items():
            self.assertEquals(dvoc.get(k), v)
        self.assertEquals(dvoc.get('NotExisting'), None)
        self.assertEquals(dvoc.get('NotExisting', 'mydefault'), 'mydefault')

    def test_getMsgId(self):
        dvoc = self.dvoc
        self.assertEquals(dvoc.getMsgid('toto1'),
                'label_cpsdir_test_dvoc_toto1_val')
        self.assertEquals(dvoc.getMsgid('NotExisting'),
                'label_cpsdir_test_dvoc_')
        self.assertEquals(dvoc.getMsgid('NotExisting', 'mydefault'),
                'label_cpsdir_test_dvoc_mydefault')

    def test_keys(self):
        dvoc = self.dvoc
        keys = self.data.keys()
        # No empty key
        dvoc.add_empty_key = False
        self.assertEquals(len(dvoc.keys()), len(keys))
        for k in dvoc.keys():
            self.assert_(k in keys)

        # Adding an empty key
        dvoc.add_empty_key = True
        self.assertEquals(len(dvoc.keys()), len(keys) + 1)
        for k in dvoc.keys():
            self.assert_(k in keys + [''])
        self.assertEquals(dvoc.keys()[0], '')

    def test_items(self):
        dvoc = self.dvoc
        items = self.data.items()
        # No empty key
        dvoc.add_empty_key = False
        self.assertEquals(len(dvoc.items()), len(items))
        for k, v in dvoc.items():
            self.assert_((k, v) in items)

        # Adding an empty key
        dvoc.add_empty_key = True
        self.assertEquals(len(dvoc.keys()), len(items) + 1)
        for k, v in dvoc.items():
            self.assert_((k, v) in items + [('', 'empty')])
        self.assertEquals(dvoc.items()[0], ('', 'empty'))

    def test_values(self):
        dvoc = self.dvoc
        values = self.data.values()
        # No empty key
        dvoc.add_empty_key = False
        self.assertEquals(len(dvoc.values()), len(values))
        for v in dvoc.values():
            self.assert_(v in values)

        # Adding an empty key
        dvoc.add_empty_key = True
        self.assertEquals(len(dvoc.keys()), len(values) + 1)
        for v in dvoc.values():
            self.assert_(v in values + ['empty'])
        self.assertEquals(dvoc.values()[0], 'empty')

    def test_has_key(self):
        dvoc = self.dvoc
        # No empty key
        dvoc.add_empty_key = False
        self.assert_(dvoc.has_key('toto1'))
        self.assert_(dvoc.has_key('toto2'))
        self.assert_(dvoc.has_key('toto3'))
        self.assert_(not dvoc.has_key(''))
        self.assert_(not dvoc.has_key('NotExisting'))

        # With empty key
        dvoc.add_empty_key = True
        self.assert_(dvoc.has_key('toto1'))
        self.assert_(dvoc.has_key('toto2'))
        self.assert_(dvoc.has_key('toto3'))
        self.assert_(dvoc.has_key(''))
        self.assert_(not dvoc.has_key('NotExisting'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryVocabulary))
    return suite

