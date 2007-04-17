##parameters=datastructure
# $Id$
"""
Do the necessary rendering or redirection after an entry has been
successfully created and filled with the initial values by the user.

The context is the directory.

May return a rendered document, or do a redirect.
"""

from urllib import urlencode

directory = context
dirname = directory.getId()
id_field = directory.id_field
id = datastructure.getDataModel()[id_field]

portal_url = context.portal_url()
args = urlencode({'dirname': dirname,
                  'id': id,
                  'portal_status_message': 'psm_entry_created',
                  })
if directory.isEditEntryAllowed(id=id):
    action_path = 'cpsdirectory_entry_edit_form'
else:
    action_path = 'cpsdirectory_entry_view'
context.REQUEST.RESPONSE.redirect('%s/%s?%s' % (portal_url, action_path, args))
