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
                'label': "label_user_name",
                'label_edit': "label_user_name",
                'description': "Member login",
                'is_i18n': 1,
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
                'label': "label_password",
                'label_edit': "label_password",
                'description': "Member password",
                'is_i18n': 1,
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
                'label': "label_roles",
                'label_edit': "label_roles",
                'description': "Member roles",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'roles',
                'size': 7,
            },
        },
        'groups': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['groups'],
                'label': "label_groups",
                'label_edit': "label_groups",
                'description': "Member groups",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'groups',
                'size': 7,
            },
        },
        'givenName': {
            'type': 'String Widget',
            'data': {
                'fields': ['givenName'],
                'label': "label_first_name",
                'label_edit': "label_first_name",
                'description': "Member first name",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
        'sn': {
            'type': 'String Widget',
            'data': {
                'fields': ['sn'],
                'label': "label_last_name",
                'label_edit': "label_last_name",
                'description': "Member last name",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
        'email': {
            'type': 'String Widget',
            'data': {
                'fields': ['email'],
                'label': "label_email",
                'label_edit': "label_email",
                'description': "Member email",
                'is_i18n': 1,
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
            [{'ncols': 1, 'widget_id': 'givenName'},
                ],
            [{'ncols': 1, 'widget_id': 'sn'},
                ],
            [{'ncols': 1, 'widget_id': 'email'},
                ],
            ],
        },
    }

members_search_layout = {
    'widgets': {
        'id': {
            'type': 'String Widget',
            'data': {
                'fields': ['id'],
                'label': "label_user_name",
                'label_edit': "label_user_name",
                'description': "Member login",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'readonly_layout_modes': ['edit'],
            },
        },
        'roles': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['roles'],
                'label': "label_roles",
                'label_edit': "label_roles",
                'description': "Member roles",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'roles',
                'size': 7,
            },
        },
        'groups': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['groups'],
                'label': "label_groups",
                'label_edit': "label_groups",
                'description': "Member groups",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'groups',
                'size': 7,
            },
        },
        'givenName': {
            'type': 'String Widget',
            'data': {
                'fields': ['givenName'],
                'label': "label_first_name",
                'label_edit': "label_first_name",
                'description': "Member first name",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
        'sn': {
            'type': 'String Widget',
            'data': {
                'fields': ['sn'],
                'label': "label_last_name",
                'label_edit': "label_last_name",
                'description': "Member last name",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
        'email': {
            'type': 'String Widget',
            'data': {
                'fields': ['email'],
                'label': "label_email",
                'label_edit': "label_email",
                'description': "Member email",
                'is_i18n': 1,
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
            [{'ncols': 1, 'widget_id': 'roles'},
                ],
            [{'ncols': 1, 'widget_id': 'groups'},
                ],
            [{'ncols': 1, 'widget_id': 'givenName'},
                ],
            [{'ncols': 1, 'widget_id': 'sn'},
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
                'label': "label_roles",
                'label_edit': "label_roles",
                'description': "",
                'is_i18n': 1,
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
                'label': "label_members",
                'label_edit': "label_members",
                'description': "",
                'is_i18n': 1,
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
                'label': "label_group",
                'label_edit': "label_group",
                'description': "",
                'is_i18n': 1,
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
                'label': "label_members",
                'label_edit': "label_members",
                'description': "",
                'is_i18n': 1,
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
    'members_search': members_search_layout,
    'roles': roles_layout,
    'groups': groups_layout,
    }

return layouts
