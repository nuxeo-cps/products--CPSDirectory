#
# Test Zope's standard UserFolder
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

#os.environ['STUPID_LOG_FILE'] = os.path.join(os.getcwd(), 'zLOG.log')
#os.environ['STUPID_LOG_SEVERITY'] = '-200'  # DEBUG

from Testing import ZopeTestCase
from Testing.ZopeTestCase import ZopeLite

ZopeLite.installProduct('CPSDirectory')

class TestExtendedAPI(ZopeTestCase.ZopeTestCase):
    def afterSetUp(self):
        self.uf = self.folder.acl_users

    def testSearchAPI(self):
        # test_user_1_ is already created. Create some more to test searching.
        self.uf.userFolderAddUser('test_user_2_','pass',['Owner'], None)
        self.uf.userFolderAddUser('test_user_3_','pass',['Manager'], None)
        self.uf.userFolderAddUser('never_returned_','pass',['Owner'], None)
        # Matching id:
        self.assert_(self.uf.searchUsers(id='test_user_1_')
            == ['test_user_1_'])
        # Partial id:
        search_opts = {'search_substring_props': ('id',)}
        res = self.uf.searchUsers(id='user', options=search_opts)
        self.assert_(len(res) == 3)
        # Several ids:
        self.assert_(len(self.uf.searchUsers(
            id=['test_user_1_', 'test_user_2_'])) == 2)
        # Roles:
        self.assert_(self.uf.searchUsers(roles='Manager') ==
            ['test_user_3_'])
        query = { 'id': 'user',
                  'roles': ['Owner', 'Manager']
                }
        self.assertEqual(self.uf.searchUsers(query=query, options=search_opts),
                         ['test_user_2_', 'test_user_3_'])
        # Do a search that returns a properties dict.
        props=['id', 'roles']
        result = self.uf.searchUsers(query=query, props=props, options=search_opts)
        self.assert_(len(result) == 2)
        # Each entry in the result should be a tuple with an id and a dictionary.
        for id, dict in result:
            # Make sure each dict has the properties asked for:
            for prop in props:
                self.assert_(prop in dict.keys())

        # Unsupported keys should mean nothing gets returned:
        query['anotherkey'] = 'shouldnotfail'
        self.assert_(self.uf.searchUsers(query=query) == [])

    def testRolesAPI(self):
        self.uf.userFolderAddUser('test_user_2_','pass',['Owner'], [])
        self.uf.userFolderAddUser('test_user_3_','pass',['Manager'], [])
        self.uf.userFolderAddUser('test_user_4_','pass',['Owner'], [])
        users = self.uf.getUsersOfRole('Manager')
        self.assert_(users == ['test_user_3_'])
        self.uf.setUsersOfRole(['test_user_4_'], 'Manager')
        users = self.uf.getUsersOfRole('Manager')
        self.assert_(users == ['test_user_4_'])
        self.uf.setUsersOfRole(['test_user_4_', 'test_user_3_'], 'Manager')
        users = tuple(self.uf.getUsersOfRole('Manager'))
        self.assert_(users == ('test_user_3_', 'test_user_4_'))
        self.uf.setRolesOfUser(['Owner'], 'test_user_4_')
        users = self.uf.getUsersOfRole('Manager')
        self.assert_(users == ['test_user_3_'])


if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
else:
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(TestExtendedAPI))
        return suite

