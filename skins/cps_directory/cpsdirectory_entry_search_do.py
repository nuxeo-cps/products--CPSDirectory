##parameters=dir, datastructure, **kw

from cgi import escape

datamodel = datastructure.getDataModel()

mapping = {}
for key, value in datamodel.items():
    if value:
        mapping[key] = value

return_fields = [x['id'] for x in
                 context.getDirectoryResultFields(dir.getId(),
                                                  dir.title_field)]

results = dir.searchEntries(return_fields=return_fields, **mapping)

rendered = dir.cpsdirectory_entry_search_results(results=results)

return rendered, 'results'
