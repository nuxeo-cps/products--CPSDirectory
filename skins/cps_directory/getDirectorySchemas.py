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
    'email': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
            },
        },
    }

###########################################################

schemas = {
    'members': members_schema,
    }

return schemas
