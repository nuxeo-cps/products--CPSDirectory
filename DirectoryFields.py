import warnings
warnings.warn(
    "%s is deprecated and has been moved to "
    "Products.CPSDirectory.fields" % __name__, DeprecationWarning, 2)

from Products.CPSDirectory.fields import *
