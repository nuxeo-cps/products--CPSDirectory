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
        'schema': 'members',
        'layout': 'members',
        'layout_style_prefix': 'layout_dir_',
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
        'schema': 'roles',
        'layout': 'roles',
        'layout_style_prefix': 'layout_dir_',
        'role_field': 'role',
        'users_field': 'users',
        'title_field': 'role',
        },
    }

#########################################################
# groups

groups_directory = {
    'type': 'CPS Groups Directory',
    'data': {
        'schema': 'groups',
        'layout': 'groups',
        'layout_style_prefix': 'layout_dir_',
        'group_field': 'group',
        'users_field': 'users',
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
