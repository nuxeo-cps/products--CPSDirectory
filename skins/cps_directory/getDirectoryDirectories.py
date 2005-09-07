##parameters=loadcustom=1
#$Id$
"""
Get the directories used.
"""

#########################################################
# members

members_directory = {
    'type': 'CPS Members Directory',
    'data': {
        'title': 'label_members',
        'schema': 'members',
        'layout': 'members',
        'schema_search': 'members_search',
        'layout_search': 'members_search',
        'id_field': 'id',
        'password_field': 'password',
        'roles_field': 'roles',
        'groups_field': 'groups',
        'title_field': 'fullname',
        'search_substring_fields': ['id', 'sn', 'givenName', 'email'],
        'acl_directory_view_roles': 'Manager; Member',
        },
    }

#########################################################
# roles

roles_directory = {
    'type': 'CPS Roles Directory',
    'data': {
        'title': 'label_roles',
        'schema': 'roles',
        'layout': 'roles',
        'layout_search': 'roles_search',
        'role_field': 'role',
        'members_field': 'members',
        'title_field': 'role',
        'search_substring_fields': ['role'],
        'acl_directory_view_roles': 'Manager',
        'acl_entry_view_roles': 'Manager',
        },
    }

#########################################################
# groups

groups_directory = {
    'type': 'CPS Groups Directory',
    'data': {
        'title': 'label_groups',
        'schema': 'groups',
        'layout': 'groups',
        'layout_search': 'groups_search',
        'group_field': 'group',
        'members_field': 'members',
        'title_field': 'group',
        'search_substring_fields': ['group'],
        'acl_directory_view_roles': 'Manager; Member',
        },
    }

#########################################################

directories = {
    'members': members_directory,
    'roles': roles_directory,
    'groups': groups_directory,
    }

if loadcustom:
    cdirectories = context.getCustomDirectories()
    directories.update(cdirectories)

return directories
