##parameters=
"""
Get the directories used.
"""
#$Id$

#########################################################
# members

members_directory = {
    'type': 'CPS Members Directory',
    'data': {
        'title': 'label_members',
        'schema': 'members',
        'schema_search': 'members_search',
        'layout': 'members',
        'layout_search': 'members_search',
        'id_field': 'id',
        'password_field': 'password',
        'roles_field': 'roles',
        'groups_field': 'groups',
        'title_field': 'id',
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
        'role_field': 'role',
        'members_field': 'members',
        'title_field': 'role',
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
        'group_field': 'group',
        'members_field': 'members',
        'title_field': 'group',
        },
    }

#########################################################

directories = {
    'members': members_directory,
    'roles': roles_directory,
    'groups': groups_directory,
    }

return directories
