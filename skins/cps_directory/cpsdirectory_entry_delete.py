##parameters=dirname, id, REQUEST=None

dir = context.portal_directories[dirname]
dir.deleteEntry(id)

if REQUEST is not None:
    portal_url = context.portal_url()
    psm = 'psm_entry_deleted'
    REQUEST.RESPONSE.redirect('%s/cpsdirectory_entry_search_form?dirname=%s'
                              '&portal_status_message=%s' %
                              (portal_url, dirname, psm))
