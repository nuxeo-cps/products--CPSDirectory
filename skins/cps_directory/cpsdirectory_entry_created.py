##parameters=datastructure
"""
Do the necessary rendering or redirection after an entry has been
successfully created and filled with the initial values by the user.

The context is the directory.

May return a rendered document, or do a redirect.
"""

from urllib import urlencode

dirname = context.getId()
id_field = context.id_field
id = datastructure.getDataModel()[id_field]

portal_url = context.portal_url()
args = urlencode({'dirname': dirname,
                  'id': id,
                  'portal_status_message': 'psm_entry_created',
                  })
action_path = 'cpsdirectory_entry_edit_form?'+args
context.REQUEST.RESPONSE.redirect('%s/%s' % (portal_url, action_path))
