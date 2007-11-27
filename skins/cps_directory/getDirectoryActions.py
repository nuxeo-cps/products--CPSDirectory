##parameters=actions, dirname, dir, mode, id=''
#$Id$
"""
Get the actions to provide on a directory view

Parameters are:
- the current actions
- the directory id
- the directory itself
- the mode (create, edit, view or search)
- the entry id (eventually)

Return the updated actions
"""

from Products.CMFCore.utils import getToolByName

utool = getToolByName(context, 'portal_url')
base_url = utool.getBaseUrl()

create_action = {
    'id': 'new_entry',
    'url': base_url+'cpsdirectory_entry_create_form?dirname='+dirname,
    'name': 'cpsdir_label_create_entry',
    'category': 'object',
    }

search_action = {
    'id': 'search_entry',
    'url': base_url+'cpsdirectory_entry_search_form?dirname='+dirname,
    'name': 'cpsdir_label_search_entry',
    'category': 'object'
    }

view_action = {
    'id': 'view_entry',
    'url': base_url+'cpsdirectory_entry_view?dirname='+dirname+'&id='+id,
    'name': 'cpsdir_label_view_entry',
    'category': 'object',
    }

edit_action = {
    'id': 'edit_entry',
    'url': base_url+'cpsdirectory_entry_edit_form?dirname='+dirname+'&id='+id,
    'name': 'cpsdir_label_edit_entry',
    'category': 'object',
    }

delete_action = {
    'id': 'delete_entry',
    'url': base_url+'cpsdirectory_entry_delete_form?dirname='+dirname+'&id='+id,
    'name': 'cpsdir_label_delete_entry',
    'category': 'object',
    }


# only actions with category 'object' have to be changed

if dir.isSearchEntriesAllowed():
    actions.update({'object': [search_action]})

if dir.isCreateEntryAllowed():
    actions['object'].append(create_action)

if mode in ['view', 'edit']:
    if dir.isViewEntryAllowed(id):
        actions['object'].append(view_action)
    if dir.isEditEntryAllowed(id):
        actions['object'].append(edit_action)
    if dir.isDeleteEntryAllowed(id):
        actions['object'].append(delete_action)

return actions
