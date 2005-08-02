from Testing import ZopeTestCase

from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CMFDefault.Portal import manage_addCMFSite

# needed products
ZopeTestCase.installProduct('ZCTextIndex', quiet=1)
ZopeTestCase.installProduct('CMFCore')
ZopeTestCase.installProduct('CMFDefault')
ZopeTestCase.installProduct('MailHost')
ZopeTestCase.installProduct('CPSSchemas')
ZopeTestCase.installProduct('CPSDocument')
ZopeTestCase.installProduct('CPSInstaller')
ZopeTestCase.installProduct('CPSDirectory')
ZopeTestCase.installProduct('CPSUserFolder')

# mandatory for CPSSchemas
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('Epoz')
# mandatory for CPSDocument
ZopeTestCase.installProduct('Localizer')
ZopeTestCase.installProduct('TranslationService')

portal_name = 'portal'

class CPSDirectoryTestCase(ZopeTestCase.PortalTestCase):

    def getPortal(self):
        if not hasattr(self.app, portal_name):
            manage_addCMFSite(self.app,
                              portal_name)
        return self.app[portal_name]

    def afterSetUp(self):
        # setup a user folder with groups instead of the standard user folder
        self.portal.manage_delObjects(['acl_users'])
        self.portal.manage_addProduct['CPSUserFolder'].addUserFolderWithGroups()
        # add back test_user_1_ that's been deleted in old acl_users, and add
        # the Manager role
        self.portal.acl_users._doAddUser('test_user_1_', '', ['Manager'], [])

        self.login('test_user_1_')

        # Set portal
        self.portal = self.getPortal()

        # Install CPSDocument using the CMF installer, its installer will call
        # the CPSSchemas installer.
        cpsdocument_cmf_installer = ExternalMethod('cpsdocument_cmf_installer',
                                                   '',
                                                   'CPSDocument.install',
                                                   'cmfinstall')
        self.portal._setObject('cpsdocument_cmf_installer',
                               cpsdocument_cmf_installer)
        self.portal.cpsdocument_cmf_installer()
        # Install CPSDirectory
        cpsdirectory_installer = ExternalMethod('cpsdirectory_installer',
                                                '',
                                                'CPSDirectory.install',
                                                'install')
        self.portal._setObject('cpsdirectory_installer', cpsdirectory_installer)
        self.portal.cpsdirectory_installer()

        # set useful nammings
        self.pd = self.portal.portal_directories
        self.pv = self.portal.portal_vocabularies

        # login as default CPS Manager
        try:
            self.login('manager')
        except AttributeError:
            manager_entry = {
                'id': 'manager',
                'sn': 'CPS',
                'givenName': 'Manager',
                'roles': ['Manager'],
                }
            self.pd.members.createEntry(manager_entry)
            self.login('manager')

    def beforeTearDown(self):
        self.logout()
