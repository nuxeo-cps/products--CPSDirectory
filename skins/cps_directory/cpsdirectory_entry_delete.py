##parameters=dirname=None, id=None, ids=[], REQUEST=None
# $Id$
"""
This script can be both called with request parameters or with form parameters
"""

from zExceptions import Forbidden

if REQUEST is None:
    raise Forbidden("Missing request")

if REQUEST.get('REQUEST_METHOD', 'GET').upper() != 'POST':
    raise Forbidden("Request must be POST")

psm = 'psm_entry_deleted'
if REQUEST.form.has_key('dirname'):
    dirname = REQUEST.form.get('dirname')

if REQUEST.form.get('ids'):
    ids = REQUEST.form.get('ids')

dir = context.portal_directories[dirname]

if id:
    try:
        dir.deleteEntry(id)
    except ValueError, e:
        msg = str(e)
        if msg.find("Operation not allowed on non-leaf") > 0:
            psm = 'psm_entry_delete_not_allowed_on_non_leaf'
        else:
            raise

if ids:
    for id in ids:
        dir.deleteEntry(id)

portal_url = context.portal_url()
REQUEST.RESPONSE.redirect('%s/cpsdirectory_entry_search_form?dirname=%s'
                          '&portal_status_message=%s' %
                          (portal_url, dirname, psm))
