##parameters=dir, datastructure, **kw

from cgi import escape

datamodel = datastructure.getDataModel()

mapping = {}
for key, value in datamodel.items():
    if value:
        mapping[key] = value

title_field = dir.title_field
results = dir.searchEntries(return_fields=[title_field], **mapping)

rendered = dir.cpsdirectory_entry_search_results(results=results)

return rendered, 'results'
