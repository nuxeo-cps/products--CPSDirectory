##parameters=dirname=None, id=None, ids=[], REQUEST=None
#
# This script can be both called with request parameters or with form parameters

from zLOG import LOG, DEBUG

logKey = 'cpsdirectory_entry_delete'

if REQUEST.form.has_key('dirname'):
    dirname = REQUEST.form.get('dirname')
    #LOG(logKey, DEBUG, "dirname = %s" % dirname)

if REQUEST.form.get('ids'):
    ids = REQUEST.form.get('ids')
    #LOG(logKey, DEBUG, "ids = %s" % str(ids))

dir = context.portal_directories[dirname]

if id:
    dir.deleteEntry(id)

if ids:
    for id in ids:
        dir.deleteEntry(id)

if REQUEST is not None:
    portal_url = context.portal_url()
    psm = 'psm_entry_deleted'
    REQUEST.RESPONSE.redirect('%s/cpsdirectory_entry_search_form?dirname=%s'
                              '&portal_status_message=%s' %
                              (portal_url, dirname, psm))
