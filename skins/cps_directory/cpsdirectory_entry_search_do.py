##parameters=dir, datastructure, **kw

from cgi import escape

datamodel = datastructure.getDataModel()

mapping = {}
for key, value in datamodel.items():
    if value:
        mapping[key] = value

result_fields = context.getDirectoryResultFields(dir.getId(),
                                                 dir.title_field)
return_fields = []
sort_by = None
sort_direction = None
for field in result_fields:
    return_fields.append(field['id'])
    sorted = field.get('sort')
    if sorted == 'asc':
        sort_by = field['id']
        sort_direction = 'asc'
    elif sorted == 'desc':
        sort_by = field['id']
        sort_direction = 'desc'

results = dir.searchEntries(return_fields=return_fields, **mapping)

if sort_by:
    items = [(item[1].get(sort_by), item) for item in results]
    items.sort()
    if sort_direction == 'desc':
        items.reverse()
    results = [item[1] for item in items]

rendered = dir.cpsdirectory_entry_search_results(results=results)

return rendered, 'results'
