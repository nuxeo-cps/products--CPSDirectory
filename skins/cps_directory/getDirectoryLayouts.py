##parameters=
"""
Get the layouts used for the directories.
"""
# $Id$

#########################################################
# members

members_layout = {
    'widgets': {
        'id': {
            'type': 'String Widget',
            'data': {
                'fields': ['id'],
                'label': "Id",
                'label_edit': "Id",
                'description': "Member login",
                'is_i18n': 0,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'readonly_layout_modes': ['edit'],
            },
        },
        'password': {
            'type': 'Password Widget',
            'data': {
                'fields': ['password'],
                'label': "Password",
                'label_edit': "Password",
                'description': "Member password",
                'is_i18n': 0,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'hidden_layout_modes': ['view', 'search'],
                'hidden_readonly_layout_modes': ['edit'],
                'hidden_empty': 1,
            },
        },
        'roles': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['roles'],
                'label': "Roles",
                'label_edit': "Roles",
                'description': "Member roles",
                'is_i18n': 0,
                'css_class': '',
                'vocabulary': 'roles',
                'size': 7,
            },
        },
        'groups': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['groups'],
                'label': "Groups",
                'label_edit': "Groups",
                'description': "Member groups",
                'is_i18n': 0,
                'css_class': '',
                'vocabulary': 'groups',
                'size': 7,
            },
        },
        'email': {
            'type': 'String Widget',
            'data': {
                'fields': ['email'],
                'label': "Email",
                'label_edit': "Email",
                'description': "Member email",
                'is_i18n': 0,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
    },
    'layout': {
        'style_prefix': 'layout_dir_',
        'ncols': 1,
        'rows': [
            [{'ncols': 1, 'widget_id': 'id'},
                ],
            [{'ncols': 1, 'widget_id': 'password'},
                ],
            [{'ncols': 1, 'widget_id': 'roles'},
                ],
            [{'ncols': 1, 'widget_id': 'groups'},
                ],
            [{'ncols': 1, 'widget_id': 'email'},
                ],
            ],
        },
    }

#########################################################
# roles

roles_layout = {
    'widgets': {
        'role': {
            'type': 'String Widget',
            'data': {
                'fields': ['role'],
                'label': "Role",
                'label_edit': "Role",
                'description': "",
                'is_i18n': 0,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'readonly_layout_modes': ['edit'],
            },
        },
        'members': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['members'],
                'label': "Members",
                'label_edit': "Members",
                'description': "",
                'is_i18n': 0,
                'css_class': '',
                'vocabulary': 'members',
                'size': 7,
            },
        },
    },
    'layout': {
        'style_prefix': 'layout_dir_',
        'ncols': 1,
        'rows': [
            [{'ncols': 1, 'widget_id': 'role'},
                ],
            [{'ncols': 1, 'widget_id': 'members'},
                ],
            ],
        },
    }

#########################################################
# groups

groups_layout = {
    'widgets': {
        'group': {
            'type': 'String Widget',
            'data': {
                'fields': ['group'],
                'label': "Group",
                'label_edit': "Group",
                'description': "",
                'is_i18n': 0,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'readonly_layout_modes': ['edit'],
            },
        },
        'members': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['members'],
                'label': "Members",
                'label_edit': "Members",
                'description': "",
                'is_i18n': 0,
                'css_class': '',
                'vocabulary': 'members',
                'size': 7,
            },
        },
    },
    'layout': {
        'style_prefix': 'layout_dir_',
        'ncols': 1,
        'rows': [
            [{'ncols': 1, 'widget_id': 'group'},
                ],
            [{'ncols': 1, 'widget_id': 'members'},
                ],
            ],
        },
    }

#########################################################

layouts = {
    'members': members_layout,
    'roles': roles_layout,
    'groups': groups_layout,
    }

return layouts
