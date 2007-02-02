#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zLOG import LOG, DEBUG, TRACE, ERROR, INFO

import unittest
from Testing.ZopeTestCase import ZopeTestCase

from AccessControl import Unauthorized
from OFS.Folder import Folder

from Products.StandardCacheManagers.RAMCacheManager import RAMCacheManager

from Products.CPSDirectory.tests.fakeCps import FakeField
from Products.CPSDirectory.tests.fakeCps import FakeListField
from Products.CPSDirectory.tests.fakeCps import FakeSchema
from Products.CPSDirectory.tests.fakeCps import FakeSchemasTool
from Products.CPSDirectory.tests.fakeCps import FakeDirectoryTool
from Products.CPSDirectory.tests.fakeCps import FakeRoot

class TestLDAPbackingDirectory(ZopeTestCase):

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

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
            'id': FakeField(),
            'dn': FakeField(),
            'cn': FakeField(),
            'foo': FakeField(),
            'bar': FakeListField(),
            })
        stool._setObject('testldapbd', s)

    def makeDir(self):
        from Products.CPSDirectory.LDAPBackingDirectory import \
                                                    LDAPBackingDirectory
        dtool = self.portal.portal_directories
        dir = LDAPBackingDirectory('ldapbackingdir',
            schema='testldapbd',
            schema_search='testldapbd',
            layout='',
            layout_search='',
            password_field='userPassword',
            title_field='cn',
            ldap_base='ou=personnes,o=nuxeo,c=com',
            ldap_scope='SUBTREE',
            ldap_search_classes='person',
            acl_directory_view_roles='test_role_1_',
            acl_entry_create_roles='test_role_1_',
            acl_entry_delete_roles='test_role_1_',
            acl_entry_view_roles='test_role_1_',
            acl_entry_edit_roles='test_role_1_',
            )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.ldapbackingdir

    def testPresence(self):
        self.assertEquals(self.pd.ldapbackingdir.meta_type, 'CPS LDAP Backing Directory')

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        self.assert_(self.dir.searchEntries() is not None)
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dir.searchEntries)

    def testEmpty(self):
        dir = self.dir
        self.assertEqual(dir.listEntryIds(), [])

    def testCreation(self):
        dir = self.dir
        id = 'chien'
        dn = 'uid=chien,ou=personnes,o=nuxeo,c=com'

        entry = {'id': id, 'foo': 'ouah', 'bar': ['4'],
             'dn': dn ,'cn': 'chien'}

        self.assertEqual(dir.listEntryIds(), [])

        self.assert_(not dir.hasEntry(id))

        self.assertRaises(KeyError, dir.getEntry, dn)

        dir.createEntry(entry)
        self.assertRaises(KeyError, dir.createEntry,
            {'id': id, 'foo': 'ouah', 'bar': ['4'], 'dn': dn ,'cn': 'chien'})

        self.assertEqual(dir.listEntryIds(), [dn])
        self.assert_(dir.hasEntry(dn))

        e = dir.getEntry(dn)
        self.assertEquals(e, {'id': id, 'foo': 'ouah', 'bar': ['4'],
             'dn': dn ,'cn': 'chien'})

        dir.deleteEntry(dn)

        self.assertEqual(dir.listEntryIds(), [])
        self.assert_(not dir.hasEntry(id))
        self.assertRaises(KeyError, dir.getEntry, dn)

    def testConvertDataToLDAP(self):
        stool = self.portal.portal_schemas
        schema = stool.testldapbd
        try:
            schema._setObject('userPassword', FakeField())
        except KeyError: # already exists
            pass

        ldir = self.dir

        # no encryption
        ldir.password_encryption = 'none'
        res = ldir.convertDataToLDAP({'userPassword': 'precious'})
        pwd = res['userPassword']
        self.assertEquals(len(pwd), 1)
        self.assertEquals(pwd[0], 'precious')

        # SSHA
        ldir.password_encryption = 'SSHA'
        res = ldir.convertDataToLDAP({'userPassword': 'precious'})
        pwd = res['userPassword']
        self.assertEquals(len(pwd), 1)
        self.assert_(pwd[0].startswith('{SSHA}'))

        # SHA
        ldir.password_encryption = 'SHA'
        res = ldir.convertDataToLDAP({'userPassword': 'precious'})
        pwd = res['userPassword']
        self.assertEquals(len(pwd), 1)
        pwd = pwd[0]
        self.assert_(pwd.startswith('{SHA}'))
        from binascii import a2b_base64
        exp = 'B\xe6:\x94\xdb\xef\xf41\x90\xf6\xc0?|X\x85\xc0\x1c\x87\xc2\x00'
        self.assertEquals(a2b_base64(pwd[5:]), exp)

        # MD5
        ldir.password_encryption = 'MD5'
        res = ldir.convertDataToLDAP({'userPassword': 'precious'})
        pwd = res['userPassword']
        self.assertEquals(len(pwd), 1)
        pwd = pwd[0]
        self.assert_(pwd.startswith('{MD5}'))
        self.assertEquals(a2b_base64(pwd[5:]),
                          '#\xf9\xd5\x0e\xcd \xcc\xc4d\xf4\xadE\xa32\x89H')

        # unknown
        ldir.password_encryption = 'parabolic'
        self.failUnlessRaises(NotImplementedError,
                              ldir.convertDataToLDAP,
                              {'userPassword': 'precious'})

        # An empty password should not be forwarded
        res = ldir.convertDataToLDAP({'userPassword': ''})
        self.assertEquals(res, {})

    def testPasswordWrites(self):
        # Encryption tests for CPSDirectory API

        stool = self.portal.portal_schemas
        schema = stool.testldapbd
        try:
            schema._setObject('userPassword', FakeField())
        except KeyError: # already exists
            pass

        ldir = self.dir
        ldir.password_encryption = 'SSHA'
        dn = 'uid=salted,ou=personnes,o=nuxeo,c=com'

        # We'll need to go low level to retrieve what has been written
        def readPwd():
            conn = ldir.connectLDAP()
            res = conn.search_s(dn, 0, '(objectClass=person)', ['userPassword'])
            # correctness of ldap call
            self.assertEquals(len(res), 1)
            self.assertEquals(res[0][0], dn)
            pwd = res[0][1]['userPassword']
            self.assertEquals(len(pwd), 1)
            return pwd[0]

        # test creation
        ldir._createEntry({'dn': dn,
                           'userPassword': 'changeme'})
        self.assert_(readPwd().startswith('{SSHA}'))

        # test edition
        ldir._editEntry({'dn': dn, 'foo': 'miaou',
                         'userPassword': 'changedme'})
        self.assert_(readPwd().startswith('{SSHA}'))

    def testPasswordReads(self):
        # all high level attempts to read password return ''
        stool = self.portal.portal_schemas
        schema = stool.testldapbd
        try:
            schema._setObject('userPassword', FakeField())
        except KeyError: # already exists
            pass

        ldir = self.dir

        dn = 'uid=me,ou=personnes,o=nuxeo,c=com'
        ldir._createEntry({'dn':dn, 'foo': 'grr', 'userPassword': 'ouah'})

        res = ldir._searchEntries(dn=dn, return_fields=['userPassword'])
        self.assertEquals(len(res), 1)
        self.assertEquals(res[0][1]['userPassword'], '')

        entry = ldir.getEntry(dn)
        self.assertEquals(entry['userPassword'], '')

    def testSearch(self):
        dir = self.dir

        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']

        dn1 = 'uid=tree,ou=personnes,o=nuxeo,c=com'

        e1 = {'id': id1, 'dn' : dn1, 'foo': foo1, 'bar': bar1, 'cn' : 'e1'}
        dir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        dn2 = 'uid=sea,ou=personnes,o=nuxeo,c=com'
        e2 = {'id': id2, 'dn' : dn2, 'foo': foo2, 'bar': bar2,  'cn' : 'e1'}

        dir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### Without substrings
        dir.search_substring_fields = []

        # Basic searches
        res = dir.searchEntries(id=id1)
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(id=[id1])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=foo1)
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=[foo1])
        self.assertEquals(res, [dn1])
        """
        fake ldap does not support multi-string search yet

        res = dir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)

        res = dir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar='a123')
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar=['a123'])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)

        res = dir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [dn1])

        # Multi-field searches
        res = dir.searchEntries(id=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [dn2])
        res = dir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [dn1])


        # Failing substring searches
        res = dir.searchEntries(id='re')
        self.assertEquals(res, [])
        res = dir.searchEntries(id='TREE')
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
        """

    def testSearchSubstrings(self):

        dir = self.dir
        id1 = 'tree'
        foo1 = 'green'
        bar1 = ['a123', 'gra']
        dn1 = 'uid=tree,ou=personnes,o=nuxeo,c=com'
        e1 = {'id': id1, 'dn' : dn1,'foo': foo1, 'bar': bar1, 'cn' : 'e1'}
        dir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        dn2 = 'uid=sea,ou=personnes,o=nuxeo,c=com'
        e2 = {'id': id2, 'dn' : dn2, 'foo': foo2, 'bar': bar2,  'cn' : 'e1'}

        dir.createEntry(e2)

        ids = [id1, id2]
        ids.sort()

        ### With substrings
        dir.search_substring_fields = ['foo', 'bar']

        # Basic searches
        res = dir.searchEntries(id=id1)
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(id=[id1])
        self.assertEquals(res, [dn1])

        """
        res = dir.searchEntries(foo=foo1)
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=[foo1])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=[foo1, foo2])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2, 'hop'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, '81'])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar='a123')
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar=['a123'])
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['gra'])
        self.assertEquals(res, ids)
        res = dir.searchEntries(bar=['a123', '8'])
        self.assertEquals(res, [dn1])

        # Multi-field searches
        res = dir.searchEntries(id=id1, foo=[foo1], bar='gra')
        self.assertEquals(res, [dn1])
        res = dir.searchEntries(foo=foo2, bar='gra')
        self.assertEquals(res, [dn2])
        res = dir.searchEntries(foo=[foo1, foo2], bar='gra')
        self.assertEquals(res, ids)
        res = dir.searchEntries(foo=[foo1, foo2], bar='a123')
        self.assertEquals(res, [dn1])

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
        """

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
        dn1 = 'uid=tree,ou=personnes,o=nuxeo,c=com'
        e1 = {'id': id1, 'dn' : dn1, 'foo': foo1, 'bar': bar1, 'cn' : 'e1'}
        zdir.createEntry(e1)

        id2 = 'sea'
        foo2 = 'blue'
        bar2 = ['812A', 'gra']
        dn2 = 'uid=sea,ou=personnes,o=nuxeo,c=com'
        e2 = {'id': id2, 'dn' : dn2, 'foo': foo2, 'bar': bar2,  'cn' : 'e1'}
        zdir.createEntry(e2)

        # cache not used yet
        self.assertEquals(getCacheReport(), [])

        # filling the cache
        res = zdir.searchEntries(id=id1)
        self.assertEquals(res, [dn1])

        # check cache is filled
        self.assertEquals(len(getCacheReport()), 1)
        self.assertEquals(getCacheReport()[0]['entries'], 1)
        self.assertEquals(getCacheReport()[0]['hits'], 0)

        # check initial result not incorrectly mutable in cache
        res.append('babar')
        res2 = zdir.searchEntries(id=id1)
        self.assertEquals(res2, [dn1])

        # check cached result not incorrectly mutable
        res.append('bibi')
        res2 = zdir.searchEntries(id=id1)
        self.assertEquals(res2, [dn1])

        # check cache is used
        self.assertEquals(getCacheReport()[0]['entries'], 1)
        self.assertEquals(getCacheReport()[0]['hits'], 2)

        # avoiding worst side-effects
        self.assertEquals(zdir.searchEntries(id=id2), [dn2])

        # check cache is filled
        self.assertEquals(len(getCacheReport()), 1)
        self.assertEquals(getCacheReport()[0]['entries'], 2)

        # changing return_fields makes a difference for the cache
        res = zdir.searchEntries(id=id1, return_fields=['bar'])
        self.assertEquals(res, [(dn1, {'dn': dn1, 'bar': ['a123', 'gra']})])

        # check not incorrectly mutable
        res.append('babar')
        res[0][1]['zap'] = 'zip'
        res[0][1]['bar'].append('zop')
        res2 = zdir.searchEntries(id=id1, return_fields=['bar'])
        self.assertEquals(res2, [(dn1, {'dn': dn1, 'bar': ['a123', 'gra']})])

        # editing entries clears the cache
        e2['foo'] = 'foo_new'
        zdir.editEntry(e2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(id=id1), [dn1])
        self.assertEquals(len(getCacheReport()), 1)

        # deleting entry clears the cache
        zdir.deleteEntry(dn2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(id=id1), [dn1])
        self.assertEquals(len(getCacheReport()), 1)

        # adding entries clears the cache
        zdir.createEntry(e2)
        self.assertEquals(len(getCacheReport()), 0)
        self.assertEquals(zdir.searchEntries(id=id1), [dn1])
        self.assertEquals(len(getCacheReport()), 1)


class TestLDAPbackingDirectoryHierarchical(ZopeTestCase):

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

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
            'id': FakeField(),
            'dn': FakeField(),
            'cn': FakeField(),
            'children': FakeListField(),
            })
        stool._setObject('testldapbd', s)

    def createEntry(self, id, children=[]):
        """Basic entry creation."""
        self.dir.createEntry({'id': id, 'cn': id,
                              'dn': '%s=%s,%s'% (self.dir.ldap_rdn_attr,
                                                 id, self.dir.ldap_base),
                              'children': children})

    def makeDir(self):
        from Products.CPSDirectory.LDAPBackingDirectory import LDAPBackingDirectory
        dtool = self.portal.portal_directories
        dir = LDAPBackingDirectory('ldapbackingdir',
                                   schema='testldapbd',
                                   schema_search='testldapbd',
                                   layout='',
                                   layout_search='',
                                   password_field='userPassword',
                                   title_field='cn',
                                   ldap_base='ou=personnes,o=nuxeo,c=com',
                                   ldap_rdn_attr='cn',
                                   ldap_scope='SUBTREE',
                                   ldap_search_classes='person',
                                   acl_directory_view_roles='test_role_1_',
                                   acl_entry_create_roles='test_role_1_',
                                   acl_entry_delete_roles='test_role_1_',
                                   acl_entry_view_roles='test_role_1_',
                                   acl_entry_edit_roles='test_role_1_',
                                   is_hierarchical=True,
                                   children_attr='children',
                                   children_id_attr='cn',
            )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool._getOb(dir.getId())
        self.createEntry('a', ['b1', 'b2', 'b3'])
        self.createEntry('b1', ['c11', 'c12'])
        self.createEntry('b2')
        self.createEntry('b3', ['c31', 'c32'])
        self.createEntry('c12')
        self.createEntry('c31')
        self.createEntry('c32')

    def test_isHierarchical(self):
        directory = self.dir
        directory.manage_changeProperties(is_hierarchical=False)
        self.assert_(not directory._isHierarchical())
        directory.manage_changeProperties(is_hierarchical=True)
        self.assert_(directory._isHierarchical())

    def test_listChildrenEntryIds(self):
        directory = self.dir
        self.assertEquals(directory._listChildrenEntryIds(
            'cn=a,ou=personnes,o=nuxeo,c=com'),
                          ['cn=b1,ou=personnes,o=nuxeo,c=com',
                           'cn=b2,ou=personnes,o=nuxeo,c=com',
                           'cn=b3,ou=personnes,o=nuxeo,c=com'])
        self.assertEquals(directory._listChildrenEntryIds(
            'cn=b3,ou=personnes,o=nuxeo,c=com'),
                          ['cn=c31,ou=personnes,o=nuxeo,c=com',
                           'cn=c32,ou=personnes,o=nuxeo,c=com'])
        self.assertEquals(directory._listChildrenEntryIds(
            'cn=b2,ou=personnes,o=nuxeo,c=com'),
                          [])

    def test_getParentEntryId(self):
        directory = self.dir
        self.assert_(directory._getParentEntryId(
            'cn=a,ou=personnes,o=nuxeo,c=com') is None)
        self.assertEquals(directory._getParentEntryId(
            'cn=c32,ou=personnes,o=nuxeo,c=com'),
                          'cn=b3,ou=personnes,o=nuxeo,c=com')
        self.assertEquals(directory._getParentEntryId(
            'cn=b2,ou=personnes,o=nuxeo,c=com'),
                          'cn=a,ou=personnes,o=nuxeo,c=com')



class TestDirectoryEntryLocalRoles(ZopeTestCase):
    # We test entry local roles on LDAPBacking directory as this is the
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
        stool._setObject('testldapbd', s)

    def makeDir(self):
        from Products.CPSDirectory.LDAPBackingDirectory import \
                                                    LDAPBackingDirectory
        dtool = self.portal.portal_directories
        # we don't ste ldap host here
        # since it's a fake ldap server
        dir = LDAPBackingDirectory('members',
            schema='testldapbd',
            schema_search='testldapbd',
            layout='',
            layout_search='',
            password_field='userPassword',
            title_field='cn',
            ldap_base='ou=personnes,o=nuxeo,c=com',
            ldap_scope='SUBTREE',
            ldap_search_classes='person',
            acl_directory_view_roles='BigSmurf',
            acl_entry_create_roles='BigSmurf; DoAlbator',
            acl_entry_delete_roles='BigSmurf; DoChapi',
            acl_entry_view_roles='BigSmurf; DoPeter',
            acl_entry_edit_roles='BigSmurf; DoPeter',
            )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.members
        res = dir.addEntryLocalRole('BigSmurf',
                'python:user_id == "test_user_1_"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoAlbator', 'python:id == "albator"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoChapi', 'python:name == "ChapiChapo"')
        self.assertEquals(res, '')
        res = dir.addEntryLocalRole('DoPeter', 'python:name == "Peterpan"')
        self.assertEquals(res, '')

        e = {'id': 'peterpan', 'name': 'Peterpan', 'cn' : 'Peter',
             'dn': 'uid=peterpan,ou=personnes,o=nuxeo,c=com',}
        self.dir.createEntry(e)

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
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
        # XXX we don't want to alllow this
        #self.assert_(meth(id='albator'))
        #self.assert_(meth(entry={'id': 'albator', 'name': 'daffy'}))
        self.assert_(not meth(id='albator'))
        self.assert_(meth(entry={'id': 'albator', 'name': 'daffy'}))

    def testDeleteEntry(self):
        meth = self.dir.isDeleteEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.assert_(meth(entry={'id': 'bzzzz', 'name': 'ChapiChapo'}))

    def testViewEntry(self):
        meth = self.dir.isViewEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.assert_(meth(entry={'name': 'Peterpan'}))
        self.assert_(meth(entry={'name': 'Blurp'}))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(entry={'name': 'Blurp'}))
        self.assert_(meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.assert_(meth(entry={'name': 'Peterpan'}))

    def testEditEntry(self):
        meth = self.dir.isEditEntryAllowed
        self.assert_(meth())
        self.assert_(meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.assert_(meth(entry={'name': 'Peterpan'}))
        self.assert_(meth(entry={'name': 'Blurp'}))
        self.logout()
        self.assert_(not meth())
        self.assert_(not meth(entry={'name': 'Blurp'}))
        self.assert_(meth(id='uid=peterpan,ou=personnes,o=nuxeo,c=com'))
        self.assert_(meth(entry={'name': 'Peterpan'}))

class TestLDAPBackingDirectoryWithBaseDNForCreation(ZopeTestCase):

    # Test the creation of an entry where the ldap_base_creation is specified

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

    def beforeTearDown(self):
        self.logout()

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
        stool._setObject('testldapbd', s)

    def makeDir(self):
        from Products.CPSDirectory.LDAPBackingDirectory import \
             LDAPBackingDirectory
        dtool = self.portal.portal_directories
        # we don't ste ldap host here
        # since it's a fake ldap server
        dir = LDAPBackingDirectory('members',
            schema='testldapbd',
            schema_search='testldapbd',
            layout='',
            layout_search='',
            password_field='userPassword',
            title_field='cn',
            ldap_base='ou=personnes,o=nuxeo,c=com',
            ldap_base_creation='ou=devels,ou=personnes,o=nuxeo,c=com',
            ldap_scope='SUBTREE',
            ldap_search_classes='person',
            ldap_rdn_attr='id',
            acl_directory_view_roles='test_role_1_',
            acl_entry_create_roles='test_role_1_',
            acl_entry_delete_roles='test_role_1_',
            acl_entry_view_roles='test_role_1_',
            acl_entry_edit_roles='test_role_1_',
            )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.members

    def test_creation_under_ldap_base_creation(self):

        dir = self.dir
        id = 'janguenot'
        dn = 'id=janguenot,ou=devels,ou=personnes,o=nuxeo,c=com'

        entry = {'id': id, 'foo': 'ouah', 'bar': ['4'],
                 'cn': 'julien'}

        dir._createEntry(entry)

        self.assertRaises(KeyError, self.dir._createEntry,
                          entry)

        self.assertEqual(dir.listEntryIds(), [dn])
        self.assert_(dir._hasEntry(dn))

        e = dir.getEntry(dn)
        self.assertEquals(e, {'id':'janguenot', 'name':''})

        dir.deleteEntry(dn)

        self.assertEqual(dir.listEntryIds(), [])
        self.assert_(not dir.hasEntry(id))
        self.assertRaises(KeyError, dir.getEntry, dn)

class TestLDAPBackingDirectoryWithSeveralSchemas(ZopeTestCase):

    # Test the behavior while adding several schemas on the directory

    def afterSetUp(self):
        ZopeTestCase.afterSetUp(self)
        self.makeSite()
        self.makeSchema()
        self.makeDir()

    def beforeTearDown(self):
        self.logout()

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
            'id': FakeField(id='id'),
            'name': FakeField(id='name'),
            'fullname' : FakeField(id='fullname',
                                   read_dep=('givenName', 'name', 'id'))
            })
        stool._setObject('testldapbd1', s)
        s = FakeSchema({
            'dn': FakeField(id='dn'),
            'givenName': FakeField(id='givenName'),
            'name' : FakeField(id='name'),
            'fullname' : FakeField(id='fullname',
                                   read_dep=('givenName', 'name', 'id'))
            })
        stool._setObject('testldapbd2', s)
        s = FakeSchema({
            'yetanotherfield': FakeField(id='yetanotherfield'),
            })
        stool._setObject('testldapbd3', s)

    def makeDir(self):
        from Products.CPSDirectory.LDAPBackingDirectory import \
             LDAPBackingDirectory
        dtool = self.portal.portal_directories
        # we don't ste ldap host here
        # since it's a fake ldap server
        dir = LDAPBackingDirectory('members',
            schema='testldapbd1 testldapbd2',
            schemas=('testldapbd3',),
            schema_search='testldapbd1',
            layout='',
            layout_search='',
            password_field='userPassword',
            title_field='cn',
            ldap_base='ou=personnes,o=nuxeo,c=com',
            ldap_base_creation='ou=devels,ou=personnes,o=nuxeo,c=com',
            ldap_scope='SUBTREE',
            ldap_search_classes='person',
            ldap_rdn_attr='id',
            acl_directory_view_roles='test_role_1_',
            acl_entry_create_roles='test_role_1_',
            acl_entry_delete_roles='test_role_1_',
            acl_entry_view_roles='test_role_1_',
            acl_entry_edit_roles='test_role_1_',
            )
        dtool._setObject(dir.getId(), dir)
        self.dir = dtool.members

    def test_getSchemas(self):
        # _getSchemas is a BBB alias for _getUniqueSchema
        schemas = self.dir._getSchemas()
        self.assertEquals(len(schemas), 1)
        unique_schema = self.dir._getUniqueSchema()
        self.assertEquals(schemas, [unique_schema])

    def test_getSchemasForSearch(self):

        search_schemas = self.dir._getSchemas(search=True)
        self.assertEqual(len(search_schemas), 1)

    def test_getFieldIds(self):

        schemas_keys = self.dir._getFieldIds()
        self.assertEqual(len(schemas_keys), 6)
        # fields are not duplicated
        schemas_keys.sort()
        self.assertEqual(schemas_keys,
                         ['dn', 'fullname', 'givenName', 'id', 'name',
                          'yetanotherfield'])

    def test_getSchemasFields(self):

        schemas_fields = self.dir._getFieldItems()
        self.assertEqual(len(schemas_fields), 6)
        schemas_keys = [x[0] for x in schemas_fields]
        schemas_keys.sort()
        self.assertEqual(schemas_keys,
                         ['dn', 'fullname', 'givenName', 'id', 'name',
                          'yetanotherfield'])
        ref_keys = self.dir._getFieldIds()
        ref_keys.sort()
        self.assertEqual(schemas_keys, ref_keys)

    def test_getFieldItemsForSearch(self):

        schemas_fields = self.dir._getFieldItems(search=True)
        self.assertEqual(len(schemas_fields), 3)
        schemas_keys = [x[0] for x in schemas_fields]
        schemas_keys.sort()
        self.assertEqual(schemas_keys,
                         ['fullname', 'id', 'name'])
        ref_keys = self.dir._getFieldIds(search=True)
        ref_keys.sort()
        self.assertEqual(schemas_keys, ref_keys)

    def test_getFieldIdsForSearch(self):

        schemas_keys = self.dir._getFieldIds(search=True)
        self.assertEqual(len(schemas_keys), 3)
        # id is not duplicated
        schemas_keys.sort()
        self.assertEqual(schemas_keys, ['fullname', 'id', 'name'])

    def test_getSchemaFieldById(self):

        field_id = 'fullname'
        deps = ['givenName', 'id', 'name']

        # Try to check it from the schema directly.
        schemas = self.dir._getSchemas()[0]
        field = schemas[field_id]
        self.assert_(field)
        rpdf = list(field.read_process_dependent_fields)
        rpdf.sort()
        self.assertEqual(rpdf, deps)

        # Try using the dedicated internal API to fetch the field
        rpdf = list(
            self.dir._getSchemaFieldById(
            field_id).read_process_dependent_fields)
        rpdf.sort()
        self.assertEqual(rpdf, deps)

    def test_getUniqueSchema(self):
        # _getUniqueSchema returns a dict to aggregate the fields of multiple
        # schemas if more than one schema is defined on the directory
        schema = self.dir._getUniqueSchema(search=False)
        self.assert_(schema)
        self.assert_(isinstance(schema, dict))

        fields = self.dir._getFieldItems()
        schema_fields = schema.items()

        field_ids = [x[0] for x in fields]
        schema_field_ids = [x[0] for x in schema_fields]

        field_ids.sort()
        schema_field_ids.sort()
        self.assertEqual(field_ids, schema_field_ids)

    def test_getUniqueSchemaForSearch(self):

        schema = self.dir._getUniqueSchema(search=True)
        self.assert_(schema)
        self.assertEqual(self.dir._getSchemas(search=True)[0], schema)

        fields = self.dir._getFieldItems(search=True)
        schema_fields = schema.items()

        field_ids = [x[0] for x in fields]
        schema_field_ids = [x[0] for x in schema_fields]

        field_ids.sort()
        schema_field_ids.sort()
        self.assertEqual(field_ids, schema_field_ids)

    def test_createEntry(self):
        entry_def = {
            'id': 'entry1',
            'dn': 'cn=entry1,ou=personnes,o=nuxeo,c=com',
            'givenName': 'Charles',
            'name': 'Darwin',
            'fullname': 'Charles Darwin',
            'yetanotherfield': 'yet anothe value',
        }
        self.dir.createEntry(entry_def)
        entries = self.dir.listEntryIds()
        self.assertEquals(entries, ['cn=entry1,ou=personnes,o=nuxeo,c=com'])

    def test_editEntry(self):
        entry_def = {
            'id': 'entry1',
            'dn': 'cn=entry1,ou=personnes,o=nuxeo,c=com',
            'givenName': 'Charles',
            'name' : 'Darwin',
            'fullname' : 'Charles Darwin',
            'yetanotherfield': 'yet another value',
        }
        self.dir.createEntry(entry_def)
        entries = self.dir.listEntryIds()
        self.assertEquals(entries, ['cn=entry1,ou=personnes,o=nuxeo,c=com'])

        entry_def['id'] = "this_id_a_new_id"
        entry_def['yetanotherfield'] = "New value for the dummy field"
        self.dir.editEntry(entry_def)
        entries = self.dir.listEntryIds()
        self.assertEquals(entries, ['cn=entry1,ou=personnes,o=nuxeo,c=com'])
        entry = self.dir.getEntry('cn=entry1,ou=personnes,o=nuxeo,c=com')
        self.assertEquals(entry, entry_def)

        # readonly behavior
        self.dir.readonly = True
        self.dir.editEntry({'yetanotherfield': "Some junk"})
        self.assertEquals(entry, entry_def)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLDAPbackingDirectory))
    suite.addTest(unittest.makeSuite(TestLDAPbackingDirectoryHierarchical))
    suite.addTest(unittest.makeSuite(TestDirectoryEntryLocalRoles))
    suite.addTest(unittest.makeSuite(
        TestLDAPBackingDirectoryWithBaseDNForCreation))
    suite.addTest(unittest.makeSuite(
        TestLDAPBackingDirectoryWithSeveralSchemas))
    return suite


if __name__ == '__main__':
    TestRunner().run(test_suite())
