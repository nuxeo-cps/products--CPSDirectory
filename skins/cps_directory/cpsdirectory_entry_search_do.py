##parameters=dir, datastructure, **kw

from cgi import escape

datamodel = datastructure.getDataModel()

mapping = {}
for key, value in datamodel.items():
    if value:
        mapping[key] = value

ids = dir.searchEntries(**mapping)

rendered = dir.cpsdirectory_entry_search_results(ids=ids)

return rendered, 'results'
