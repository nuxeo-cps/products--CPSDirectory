##parameters=dirname, id, REQUEST

dir = context.portal_directories[dirname]
dir.deleteEntry(id)

return dir.cpsdirectory_entry_search_form(dirname=dirname)
