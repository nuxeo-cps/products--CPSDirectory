# -*- encoding: iso-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Anahide Tchertchian <at@nuxeo.com>
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
from AccessControl import Unauthorized
from CPSDirectoryTestCase import CPSDirectoryTestCase

class TestIndirectDirectory(CPSDirectoryTestCase):

    def afterSetUp(self):
        CPSDirectoryTestCase.afterSetUp(self)
        self.makeDir()

    def makeDir(self):
        """
        Make a test ZODB dir and an indirect dir prointing towards it, in order
        to make tests
        """

        stool = self.portal.portal_schemas
        schema = stool.manage_addCPSSchema('testindirectdir')
        schema.manage_addField('id', 'CPS String Field')
        schema.manage_addField('surname', 'CPS String Field')
        field = schema.manage_addField('fullname', 'CPS String Field')
        # make it a computed field
        field.manage_changeProperties(
            default_expr='string:',
            acl_write_roles='Nobody',
            read_ignore_storage=1,
            read_process_expr="python:surname or len(id.split('/'))>1 and id.split('/')[1] or id",
            read_process_dependent_fields=['surname', 'id'],
            write_ignore_storage=1,
            )

        zodbdir = self.pd.manage_addCPSDirectory('zodbdir',
                                                 'CPS ZODB Directory')
        zodbdir.manage_changeProperties(
            schema='testindirectdir',
            schema_search='testindirectdir',
            layout='',
            layout_search='',
            id_field='id',
            title_field='fullname',
            search_substring_fields= ('id', 'fullname'),
            acl_directory_view_roles='Manager',
            acl_entry_create_roles='Manager',
            acl_entry_delete_roles='Manager',
            acl_entry_view_roles='Manager',
            acl_entry_edit_roles='Manager',
            )
        # add entries to the zodb dir
        zodbdir.createEntry({'id': 'juanita', 'surname': 'Juanita',})
        zodbdir.createEntry({'id': 'juan'})
        self.zodbdir = zodbdir

        dir = self.pd.manage_addCPSDirectory('indirectdir',
                                             'CPS Indirect Directory')
        dir.manage_changeProperties(
            schema='testindirectdir',
            schema_search='testindirectdir',
            layout='',
            layout_search='',
            id_field='id',
            title_field='fullname',
            search_substring_fields=('id',),
            directory_ids=('zodbdir',),
            acl_directory_view_roles='Manager',
            acl_entry_create_roles='Manager',
            acl_entry_delete_roles='Manager',
            acl_entry_view_roles='Manager',
            acl_entry_edit_roles='Manager',
            )
        self.dir = dir


    #
    # Tests begin here
    #

    def testPresence(self):
        self.assertEquals(self.pd.indirectdir.meta_type, 'CPS Indirect Directory')

    def testBasicSecurity(self):
        self.assert_(self.dir.isVisible())
        self.assert_(self.dir.isCreateEntryAllowed())
        self.assert_(self.dir.searchEntries() is not None)
        self.logout()
        self.assert_(not self.dir.isVisible())
        self.assert_(not self.dir.isCreateEntryAllowed())
        self.assertRaises(Unauthorized, self.dir.searchEntries)

    def testEmpty(self):
        self.assertEqual(self.dir.listEntryIds(), [])

    def testCreation(self):
        self.assertEqual(self.dir.listEntryIds(), [])
        self.assert_(not self.dir.hasEntry('juan'))
        self.assert_(not self.dir.hasEntry('zodbdir/juan'))

        # create entry
        self.dir.createEntry({'id': 'zodbdir/juan'})

        self.assertEqual(self.dir.listEntryIds(), ['zodbdir/juan'])
        self.assert_(not self.dir.hasEntry('juan'))
        self.assert_(self.dir.hasEntry('zodbdir/juan'))

    def test_listEntryIds(self):
        self.assertEqual(self.dir.listEntryIds(), [])
        self.dir.createEntry({'id': 'zodbdir/juan'})
        self.assertEqual(self.dir.listEntryIds(),
                         ['zodbdir/juan'])
        self.dir.createEntry({'id': 'zodbdir/juanita'})
        self.assertEqual(self.dir.listEntryIds(),
                         ['zodbdir/juan', 'zodbdir/juanita'])
        self.dir.deleteEntry('zodbdir/juanita')
        self.assertEqual(self.dir.listEntryIds(),
                         ['zodbdir/juan'])

    def test_listEntryIdsAndTitles(self):
        self.assertEqual(self.dir.listEntryIdsAndTitles(), [])
        self.dir.createEntry({'id': 'zodbdir/juan'})
        self.assertEqual(self.dir.listEntryIdsAndTitles(),
                         [('zodbdir/juan', 'juan'),])
        self.dir.createEntry({'id': 'zodbdir/juanita'})
        self.assertEqual(self.dir.listEntryIdsAndTitles(),
                         [('zodbdir/juan', 'juan'),
                          ('zodbdir/juanita', 'Juanita'),
                          ])


    def test_listAllPossibleEntriesIds(self):
        self.assertEqual(self.dir.listAllPossibleEntriesIds(),
                         ['zodbdir/juan', 'zodbdir/juanita'])

    def test_listAllPossibleEntriesIdsAndTitles(self):
        self.assertEqual(self.dir.listAllPossibleEntriesIdsAndTitles(),
                         [('zodbdir/juan', 'juan'),
                          ('zodbdir/juanita', 'Juanita'),
                          ])


    def test_makeId(self):
        self.assertEqual(self.dir._makeId('truc', 'muche'),
                         'truc/muche')

    def test_getDirctory(self):
        self.assertEqual(self.dir._getDirectory('zodbdir'),
                         self.zodbdir)
        self.assertRaises(AttributeError,
                          self.dir._getDirectory,
                          'bidule')
        self.pd.manage_delObjects(['zodbdir'])
        self.assertRaises(AttributeError,
                          self.dir._getDirectory,
                          'zodbdir')

    def test_getDirectoryIdForId(self):
        self.assertEqual(self.dir._getDirectoryIdForId('truc/muche'),
                         'truc')

    def test_getEntryIdForId(self):
        self.assertEqual(self.dir._getEntryIdForId('truc/muche'),
                         'muche')

    # XXX Still to test:

    #def hasEntry(self, id):
    #def _createEntry(self, entry):
    #def deleteEntry(self, id):
    #def _searchEntries(self, return_fields=None, **kw):
    #def searchPossibleEntries(self, return_fields=None, **kw):
    #def formatSearchResults(self, return_fields, directory_id, results):

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIndirectDirectory))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=2)
