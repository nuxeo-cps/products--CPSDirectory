# -*- coding: ISO-8859-15 -*-
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Tarek Ziadé <tz@nuxeo.com>
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
from Acquisition import Implicit

from Products.CPSDirectory.DirectoryWidgets import CPSUserIdentifierWidget

class FakePortal(Implicit):
    pass
fakePortal = FakePortal()

class FakeUrlTool(Implicit):
    def getPortalObject(self):
        return fakePortal

class FakeTranslationService:
    def getSelectedLanguage(self):
        return 'fr'

fakePortal.portal_url = FakeUrlTool()
fakePortal.portal_workflow = None
fakePortal.translation_service = FakeTranslationService()

class TestDirectoryWidgets(unittest.TestCase):

    def test_CPSUserIdentifierWidget(self):
       wi = CPSUserIdentifierWidget('widget_id').__of__(fakePortal)
       self.assert_(not wi._checkIdentifier('136ll'))
       self.assert_(not wi._checkIdentifier('é"136ll'))
       wi.id_pat = r'[a-zA-Z0-9@\-\._]*$'
       self.assert_(wi._checkIdentifier('136ll'))
       self.assert_(not wi._checkIdentifier('é"136ll'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestDirectoryWidgets),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
