from Testing import ZopeTestCase
from Products.CPSDefault.tests import CPSTestCase

# XXX: only CPSSchemas and CPSDirectory should be mandatory here
ZopeTestCase.installProduct('CPSDocument')
ZopeTestCase.installProduct('CPSSchemas')
ZopeTestCase.installProduct('PortalTransforms')
ZopeTestCase.installProduct('Epoz')
ZopeTestCase.installProduct('CPSDirectory')

CPSTestCase.setupPortal()

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

class CPSDirectoryTestCase(CPSTestCase.CPSTestCase):

    def afterSetUp(self):
        print_log_errors(zLOG.WARNING)

    def beforeTearDown(self):
        ignore_log_errors()
