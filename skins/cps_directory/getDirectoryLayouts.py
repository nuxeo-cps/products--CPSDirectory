##parameters=loadcustom=1
# $Id$
"""
Get the layouts used for the directories.
"""

#########################################################
# members

members_layout = {
    'widgets': {
        'id': {
            'type': 'User Identifier Widget',
            'data': {
                'fields': ['id'],
                'label': "label_user_name",
                'label_edit': "label_user_name",
                'description': "Member login",
                'is_required': 1,
                'is_i18n': 1,
                'css_class': '',
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
        'confirm': {
            'type': 'Password Widget',
            'data': {
                'fields': ['confirm'],
                'label': 'label_password_confirm',
                'label_edit': 'label_password_confirm',
                'description': 'Password confirmation when editing',
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
                'hidden_layout_modes': ['view', 'search'],
                'hidden_readonly_layout_modes': ['edit'],
                'hidden_empty': 1,
                'password_widget': 'password',
            },
        },
        'roles': {
            'type': 'Generic MultiSelect Widget',
            'data': {
                'fields': ['roles'],
                'label': "label_roles",
                'label_edit': "label_roles",
                'description': "Member roles",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'global_roles',
                'render_format': 'checkbox',
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
                'is_required': 1,
                'is_i18n': 1,
                'css_class': '',
                'display_width': 20,
                'size_max': 0,
            },
        },
        'fullname': {
            'type': 'String Widget',
            'data': {
                'fields': ['fullname'],
                'label': "label_full_name",
                'label_edit': "label_full_name",
                'description': "Member full name",
                'is_i18n': 1,
                'css_class': '',
                'display_width': 30,
                'size_max': 0,
                'hidden_layout_modes': ['create', 'edit', 'search'],
            },
        },
        'email': {
            'type': 'Email Widget',
            'data': {
                'fields': ['email'],
                'label': "label_email",
                'label_edit': "label_email",
                'description': "Member email",
                'is_required': 1,
                'is_i18n': 1,
                'css_class': '',
                'display_width': 30,
                'size_max': 0,
                },
            },
        'homeless': {
            'type': 'Boolean Widget',
            'data': {
                'fields': ['homeless'],
                'label': 'cpsdir_label_homeless',
                'label_edit': 'cpsdir_label_homeless',
                'help': 'cpsdir_help_homeless',
                'description': "Homeless ?",
                'is_i18n': 1,
                'css_class': '',
                'label_false': 'cpsschemas_label_true',
                'label_true': 'cpsschemas_label_false',
                },
            },
        },
    'layout': {
        'style_prefix': 'layout_dir_',
        'ncols': 2,
        'rows': [
            [{'widget_id': 'id'},],
            [{'widget_id': 'password'},],
            [{'widget_id': 'confirm'},],
            [{'widget_id': 'givenName'}, {'widget_id': 'sn'},],
            [{'widget_id': 'fullname'},],
            [{'widget_id': 'email'},],
            [{'widget_id': 'roles'}, {'widget_id': 'groups'},],
            [{'widget_id': 'homeless'},],
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
                'display_width': 30,
                'is_i18n': 1,
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
                'display_width': 20,
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
                'display_width': 20,
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
                'display_width': 30,
            },
        },
    },
    'layout': {
        'style_prefix': 'layout_dir_',
        'ncols': 2,
        'rows': [
            [{'widget_id': 'id'},],
            [{'widget_id': 'givenName'}, {'widget_id': 'sn'},],
            [{'widget_id': 'email'},],
            [{'widget_id': 'groups'},],
            ],
        },
    }


#########################################################
# roles

roles_layout = {
    'widgets': {
        'role': {
            'type': 'Identifier Widget',
            'data': {
                'fields': ['role'],
                'label': "label_roles",
                'label_edit': "label_roles",
                'is_required': 1,
                'is_i18n': 1,
                'display_width': 20,
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

roles_search_layout = {
    'widgets': {
        'role': {
            'type': 'String Widget',
            'data': {
                'fields': ['role'],
                'label': "label_roles",
                'label_edit': "label_roles",
                'is_i18n': 1,
                'display_width': 20,
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
            'type': 'Identifier Widget',
            'data': {
                'fields': ['group'],
                'label': "label_group",
                'label_edit': "label_group",
                'is_required': 1,
                'is_i18n': 1,
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
        'subgroups': {
            'type': 'MultiSelect Widget',
            'data': {
                'fields': ['subgroups'],
                'label': "label_subgroups",
                'label_edit': "label_subgroups",
                'description': "",
                'is_i18n': 1,
                'css_class': '',
                'vocabulary': 'groups',
                'size': 7,
                'hidden_if_expr':
                    'not:context/hasSubGroupsSupport',
                'hidden_layout_modes': 'search',
                'hidden_readonly_layout_modes': 'edit create view'
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
            [{'ncols': 1, 'widget_id': 'subgroups'},
                ],
            ],
        },
    }

groups_search_layout = {
    'widgets': {
        'group': {
            'type': 'String Widget',
            'data': {
                'fields': ['group'],
                'label': "label_group",
                'label_edit': "label_group",
                'is_i18n': 1,
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
    'roles_search': roles_search_layout,
    'groups': groups_layout,
    'groups_search': groups_search_layout,
    }

if loadcustom:
    clayouts = context.getCustomDirectoryLayouts()
    layouts.update(clayouts)

return layouts
