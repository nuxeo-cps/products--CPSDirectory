##parameters=dirname=None, id=None, ids=[], REQUEST=None
# $Id$
"""
This script can be both called with request parameters or with form parameters
"""

from zExceptions import Forbidden
from Products.CMFCore.utils import getToolByName

if REQUEST is None:
    raise Forbidden("Missing request")

if REQUEST.get('REQUEST_METHOD', 'GET').upper() != 'POST':
    raise Forbidden("Request must be POST")

utool = getToolByName(context, 'portal_url')
portal = utool.getPortalObject()

psm = 'psm_entry_deleted'
if REQUEST.form.has_key('dirname'):
    dirname = REQUEST.form.get('dirname')

if REQUEST.form.get('ids'):
    ids = REQUEST.form.get('ids')


dir = portal.portal_directories[dirname]
 
if REQUEST.form.has_key('archive_user_spaces'):
    # Archiving all the folders of members if those folders exist.
    # Archiving in this context means renaming the directory with a prefix
    # "archive-" and removing all the permissions associated
    # to the previous owner.
    mtool = portal.portal_membership
    members_folder_rpath = mtool.getProperty('membersfolder_id')
    members_folder = portal[members_folder_rpath]
    for uid in ids:
        member_folder = members_folder.restrictedTraverse(uid, default=None)
        if member_folder is not None:
            members_folder.manage_renameObject(uid, 'archive-' + uid)
            title_old = member_folder.Title()
            doc = member_folder.getEditableContent()
            doc.edit(Title="(Archived) " + title_old)
            mtool.deleteLocalRoles(member_folder, [uid], recursive=True)


if id:
    try:
        dir.deleteEntry(id)
    except ValueError, e:
        msg = str(e)
        if msg.find("Operation not allowed on non-leaf") > 0:
            psm = 'psm_entry_delete_not_allowed_on_non_leaf'
        else:
            raise

if ids:
    for id in ids:
        dir.deleteEntry(id)
    if len(ids) > 1:
        psm = 'psm_entries_deleted'

REQUEST.RESPONSE.redirect('%s/cpsdirectory_entry_search_form?dirname=%s'
                          '&portal_status_message=%s' %
                          (portal.absolute_url(), dirname, psm))
