##parameters=directory_id, default_field='id'
"""
Get the list of fields to be displayed in the search result list.

Format is [{'id': 'sn', 'title': 'Name'}, ] title will be i18n.
see getCustomDirectoryResultFields for more information
"""
fields = context.getCustomDirectoryResultFields(directory_id, default_field)

dir = getattr(context.portal_directories, directory_id)
id_field = getattr(dir, 'id_field', 'id')
title_field = getattr(dir, 'title_field', 'title')

if not fields:
    if directory_id == 'members':
        fields = [{'id': 'sn', 'title': 'label_last_name', 'sort': 'asc'},
                  {'id': 'givenName', 'title': 'label_first_name'},
                  {'id': 'email', 'title': 'label_email'},
                  {'id': id_field, 'title': 'label_id'},
                  ]
    elif directory_id == 'groups':
        fields = [{'id': id_field, 'title': 'label_group', 'sort': 'asc'},]
    elif directory_id == 'roles':
        fields = [{'id': id_field, 'title': 'label_roles', 'sort': 'asc'},]

if not fields:
    fields = [{'id': id_field, 'title': 'Id'},
              {'id': title_field, 'title': 'Title', 'sort': 'asc'}]

return fields
