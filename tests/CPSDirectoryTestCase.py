# Copyright (c) 2003-2006 Nuxeo SAS <http://nuxeo.com>
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

from Products.CPSDefault.tests.CPSTestCase import CPSTestCase, MANAGER_ID

# XXX FIXME: use a special profile installing what's needed for CPSDirectory to
# work, e.g:
# - CMF
# - CPSUserFolder
# - CPSDocument FlexibleTypeInformation
# - CPSSchemas tools
# - CPSDirectory
# - default portal, user folder, directories, layouts and schemas

class CPSDirectoryTestCase(CPSTestCase):

    def afterSetUp(self):
        self.login(MANAGER_ID)
        CPSTestCase.afterSetUp(self)
        # set useful nammings
        self.pd = self.portal.portal_directories
        self.pv = self.portal.portal_vocabularies

    def beforeTearDown(self):
        CPSTestCase.beforeTearDown(self)
        self.logout()
