##parameters=
"""
Get the schemas used for the directories.
"""
#$Id$

#########################################################
# members

members_schema = {
    'id': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
            },
        },
    'password': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'roles': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'groups': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'email': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
            },
        },
    }

#########################################################
# roles

roles_schema = {
    'role': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
            },
        },
    'users': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    }

#########################################################
# groups

groups_schema = {
    'group': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
            },
        },
    'users': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    }

#########################################################

schemas = {
    'members': members_schema,
    'roles': roles_schema,
    'groups': groups_schema,
    }

return schemas
