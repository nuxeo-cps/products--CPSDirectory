##parameters=directory_id, default_field='id'
"""
Get the list of fields to be displayed in the search result list.

Format is [{'id': 'sn', 'title': 'Name'}, ] title will be i18n.
see getCustomDirectoryResultFields for more information
"""
fields = context.getCustomDirectoryResultFields(directory_id, default_field)

if not fields:
    if directory_id == 'members':
        fields = [{'id': 'sn', 'title': 'label_last_name'},
                  {'id': 'givenName', 'title': 'label_first_name'},
                  {'id': 'id', 'title': 'label_user_name'},
                  ]
    elif directory_id == 'groups':
        fields = [{'id': 'group', 'title': 'label_group'},]
    elif directory_id == 'roles':
        fields = [{'id': 'role', 'title': 'label_roles'},]

if not fields:
    dir = getattr(context.portal_directories, directory_id)
    fields = [{'id': dir.id_field, 'title': 'Id'},
              {'id': dir.title_field, 'title': 'Title'}]

return fields
