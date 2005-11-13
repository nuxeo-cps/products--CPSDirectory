# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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

import os
from zLOG import LOG, INFO, DEBUG

from Products.CPSInstaller.CPSInstaller import CPSInstaller



def install(self):

    installer = CPSInstaller(self, 'CPSDirectory')
    installer.log("Starting CPSDirectory install")
    # skins
    skins = {'cps_directory': 'Products/CPSDirectory/skins/cps_directory',}
    installer.verifySkins(skins)
    installer.resetSkinCache() #Needed to find the schema methods below
    installer.verifyTool('portal_directories', 'CPSDirectory',
                         'CPS Directory Tool')
    installer.verifyDirectories(self.getDirectoryDirectories())

    installer.verifySchemas(self.getDirectorySchemas())
    installer.verifyLayouts(self.getDirectoryLayouts())
    installer.verifyVocabularies(self.getDirectoryVocabularies())

    mdir = installer.getTool('portal_directories')['members']
    try:
        #
        # Update the member data from the schema if we are
        # using a CPS Members Directory
        #
        mdir.manage_updateMemberDataFromSchema()
    except AttributeError:
        #
        # Here, CPS LDAP Directory for members
        #
        installer.log("LDAP User Groups Folder")

    installer.setupTranslations()
    installer.verifyAction(
                'portal_actions',
                id='directories',
                name='Directories',
                action='string:${portal_url}/cpsdirectory_view',
                condition='python:'
                    'not portal.portal_membership.isAnonymousUser()',
                permission=('View',),
                category='global',
                visible=1)

    installer.finalize()
    installer.log("End of specific CPSDirectory install")
    return installer.logResult()
