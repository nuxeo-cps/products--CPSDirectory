##parameters=key=None,is_i18n=False
#
# $Id$
"""Return all the roles of the roles directory, as a list of tuples.

This method is to be used within a Method vocabulary.

By contract to the MethodVocabulary class this method should handle a "key"
argument :

* If the key is None, all the values of the vocabulary should be returned.

* If the key is not None then the method must return a value corresponding to
  this key. But if nothing was found corresponding to this key, a KeyError
  should be raised.
"""

from logging import getLogger

from Products.CMFCore.utils import getToolByName

LOG_KEY = 'getGlobalRoles'
logger = getLogger(LOG_KEY)

portal = getToolByName(context, 'portal_url').getPortalObject()
cpsmcat = portal.Localizer.default
dtool = portal.portal_directories
roles_directory = dtool.roles
charset = portal.default_charset

marker = []
value = marker
returned = []

## logger.debug("key = %s" % str(key))

entries_ids = roles_directory.searchEntries()
for entry_id in entries_ids:
    if is_i18n:
        msgid = 'label_cpsdir_roles_' + entry_id
        label = cpsmcat(msgid).encode(charset, 'ignore')
    else:
        label = entry_id

    if key is None:
        returned.append((entry_id, label))
    elif entry_id == key:
        value = label
        break

if key is not None:
##     logger.debug("value = %s" % str(value))
    if value is not marker:
        return value
    else:
        # This case will be catched by the MethodVocabulary which will return
        # a default value.
        raise KeyError
else:
    return returned
