##parameters=datastructure
"""
Do the necessary rendering or redirection after an entry has been
successfully created and filled with the initial values by the user.

The context is the directory.

May return a rendered document, or do a redirect.
"""

dirname = context.getId()
id_field = context.id_field
id = datastructure.getDataModel()[id_field]

portal_url = context.portal_url()
action_path = 'cpsdirectory_entry_edit_form?dirname=%s&id=%s' % (
    dirname, id)
psm = 'psm_entry_created'
context.REQUEST.RESPONSE.redirect('%s/%s&portal_status_message=%s' %
                                  (portal_url, action_path, psm))
