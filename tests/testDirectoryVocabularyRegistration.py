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
"""Integration tests on vocabulary registration
"""
from Testing import ZopeTestCase
import unittest

# Installing CPSDirectory to trigger registrations
ZopeTestCase.installProduct('CPSDirectory')

class TestDirectoryVocabularyRegistration(unittest.TestCase):

    def testIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Vocabulary' in VTR.listTypes())
        self.assertEquals(VTR.getType('CPS Directory Vocabulary').meta_type,
            'CPS Directory Vocabulary')

    def testDirectoryEntryVocabulatryIsRegistered(self):
        from Products.CPSSchemas.VocabulariesTool \
            import VocabularyTypeRegistry as VTR
        self.assert_('CPS Directory Entry Vocabulary' in VTR.listTypes())
        meta_type = VTR.getType('CPS Directory Entry Vocabulary').meta_type
        self.assertEquals(meta_type, 'CPS Directory Entry Vocabulary')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDirectoryVocabularyRegistration))
    return suite
