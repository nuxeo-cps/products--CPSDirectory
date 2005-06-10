##parameters=REQUEST, dirname, dir, dirtitle
#$Id$
"""
Set breadcrumbs in directory pages
"""

from zLOG import LOG, DEBUG

directories_breadcrumb = {
    'id': 'directories',
    'url': context.portal_url() + '/cpsdirectory_view',
    'title': context.translation_service('Directories'),
    }

directory_breadcrumbs = {
    'id': 'directories',
    'url': context.portal_url() + '/cpsdirectory_entry_search_form?dirname=' + dirname,
    'title': context.translation_service(dirtitle),
    }

breadcrumb_set = [directories_breadcrumb]

if dir.isVisible():
    breadcrumb_set.append(directory_breadcrumbs)

REQUEST.set('breadcrumb_set', breadcrumb_set)
