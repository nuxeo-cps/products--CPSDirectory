##parameters=directory_id, default_field='id'
"""
Get the list of fields to be displayed in the search result list.

Format is [{'id': 'sn', 'title': 'Name'}, ] title will be i18n.
"""
fields = context.getCustomDirectoryResultFields(directory_id, default_field)
if not fields:
    fields = [{'id': default_field,
               'title': 'Id'}]

return fields
