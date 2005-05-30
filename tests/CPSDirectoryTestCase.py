# Perform replacements in sys.modules to be able to run tests with fake ldap
# classes/methods
from Testing import ZopeTestCase

from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.CMFDefault.Portal import manage_addCMFSite

# Perform replacements in sys.modules to be able to run tests with fake ldap
# classes/methods
from Products.CPSDirectory.tests.ldap import importer

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

import zLOG

def print_log_errors(min_severity=zLOG.INFO):
    if hasattr(zLOG, 'old_log_write'):
        return
    def log_write(subsystem, severity, summary, detail, error,
                  PROBLEM=zLOG.PROBLEM, min_severity=min_severity):
        if severity >= min_severity:
            print "%s(%s): %s, %s" % (subsystem, severity, summary, detail)
    zLOG.old_log_write = zLOG.log_write
    zLOG.log_write = log_write

def ignore_log_errors():
    if hasattr(zLOG, 'old_log_write'):
        zLOG.log_write = zLOG.old_log_write
        del zLOG.old_log_write

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

        print_log_errors(zLOG.WARNING)

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
        ignore_log_errors()
