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
cpsmcat = portal.translation_service
dtool = portal.portal_directories
roles_directory = dtool.roles
charset = portal.default_charset

returned = []

## logger.debug("key = %s" % str(key))
if key is None:
    entries_ids = roles_directory.searchEntries()
    for entry_id in entries_ids:
        if is_i18n:
            msgid = 'label_cpsdir_roles_' + entry_id
            label = cpsmcat(msgid).encode(charset, 'ignore')
        else:
            label = entry_id
        returned.append((entry_id, label))
    return returned

else:
    entry_id = key
    if roles_directory.hasEntry(entry_id):
        if is_i18n:
            msgid = 'label_cpsdir_roles_' + entry_id
            label = cpsmcat(msgid).encode(charset, 'ignore')
        else:
            label = entry_id
        return label
    else:
        # This case will be catched by the MethodVocabulary which will return
        # a default value.
        raise KeyError
