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
                'is_i18n': 0,
                'label_edit': 'Id',
                'label': 'Id',
                'description': 'Member login',
                'css_class': '',
                'is_required': 1,
                'display_width': 20,
                'size_max': 0,
            },
        },
        'password': {
            'type': 'Password Widget',
            'data': {
                'fields': ['password'],
                'is_i18n': 0,
                'label_edit': 'Password',
                'label': 'Password',
                'description': 'Member password',
                'css_class': '',
                'is_required': 1,
                'hidden_view': 1,
                'display_width': 20,
                'size_max': 0,
            },
        },
        'roles': {
            'type': 'String Widget',
            'data': {
                'fields': ['roles'],
                'is_i18n': 0,
                'label_edit': 'Roles',
                'label': 'Roles',
                'description': 'Member roles',
                'css_class': '',
                'is_required': 1,
                'display_width': 40,
                'size_max': 0,
            },
        },
        'groups': {
            'type': 'String Widget',
            'data': {
                'fields': ['groups'],
                'is_i18n': 0,
                'label_edit': 'Groups',
                'label': 'Groups',
                'description': 'Member groups',
                'css_class': '',
                'is_required': 1,
                'display_width': 40,
                'size_max': 0,
            },
        },
        'email': {
            'type': 'String Widget',
            'data': {
                'fields': ['email'],
                'is_i18n': 0,
                'label_edit': 'Email',
                'label': 'Email',
                'description': 'Member email',
                'css_class': '',
                'is_required': 1,
                'display_width': 20,
                'size_max': 0,
            },
        },
    },
    'layout': {
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
                'is_i18n': 0,
                'label_edit': 'Role',
                'label': 'Role',
                'description': '',
                'css_class': '',
                'is_required': 1,
                'display_width': 20,
                'size_max': 0,
            },
        },
        'users': {
            'type': 'String Widget',
            'data': {
                'fields': ['users'],
                'is_i18n': 0,
                'label_edit': 'Users',
                'label': 'Users',
                'description': '',
                'css_class': '',
                'is_required': 1,
                'display_width': 40,
                'size_max': 0,
            },
        },
    },
    'layout': {
        'ncols': 1,
        'rows': [
            [{'ncols': 1, 'widget_id': 'role'},
                ],
            [{'ncols': 1, 'widget_id': 'users'},
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
                'is_i18n': 0,
                'label_edit': 'Group',
                'label': 'Group',
                'description': '',
                'css_class': '',
                'is_required': 1,
                'display_width': 20,
                'size_max': 0,
            },
        },
        'users': {
            'type': 'String Widget',
            'data': {
                'fields': ['users'],
                'is_i18n': 0,
                'label_edit': 'Users',
                'label': 'Users',
                'description': '',
                'css_class': '',
                'is_required': 1,
                'display_width': 40,
                'size_max': 0,
            },
        },
    },
    'layout': {
        'ncols': 1,
        'rows': [
            [{'ncols': 1, 'widget_id': 'group'},
                ],
            [{'ncols': 1, 'widget_id': 'users'},
                ],
            ],
        },
    }

#########################################################

layouts = {
    'members': members_layout,
    'roles': roles_layout,
    'goups': groups_layout,
    }

return layouts
