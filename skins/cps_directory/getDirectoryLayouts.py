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
                'display_width': 40,
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
                'display_width': 40,
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
            [{'ncols': 1, 'widget_id': 'email'},
                ],
            ],
        },
    }

###########################################################

layouts = {
    'members': members_layout,
    }

return layouts
