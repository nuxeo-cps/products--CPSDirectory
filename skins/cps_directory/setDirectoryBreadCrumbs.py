##parameters=REQUEST, dirname, dir, dirtitle
#$Id$
"""
Set breadcrumbs for the directories pages.
"""

from Products.CMFCore.utils import getToolByName

utool = getToolByName(context, 'portal_url')
portal = utool.getPortalObject()
portal_url = portal.absolute_url()

portal_root_breadcrumb = {
    'id': portal.getId(),
    'url': portal_url,
    'title': portal.Title(),
    }

directories_breadcrumb = {
    'id': 'directories',
    'url': portal_url + '/cpsdirectory_view',
    'title': context.translation_service('Directories'),
    }

breadcrumb_set = [portal_root_breadcrumb, directories_breadcrumb]

if dir.isVisible():
    directory_breadcrumbs = {
        'id': 'directories',
        'url': portal_url + '/cpsdirectory_entry_search_form?dirname=' + dirname,
        'title': context.translation_service(dirtitle),
        }
    breadcrumb_set.append(directory_breadcrumbs)

REQUEST.set('breadcrumb_set', breadcrumb_set)
