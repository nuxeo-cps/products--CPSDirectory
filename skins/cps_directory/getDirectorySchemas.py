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
        'type': 'CPS Password Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'roles': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles': 'Manager',
            },
        },
    'groups': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles': 'Manager',
            },
        },
    'givenName': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'sn': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'fullname': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
                'acl_write_roles': 'Nobody',
                'read_ignore_storage': 1,
                'read_process_expr': 'python: givenName+" "+sn',
                'read_process_dependent_fields': ['givenName', 'sn'],
                'write_ignore_storage': 1,
            },
        },
    'email': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 1,
                'acl_write_roles': 'Manager; Owner',
            },
        },
    }

members_search_schema = {
    'id': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'roles': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'groups': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'givenName': {
        'type': 'CPS String Field',
        'data': {
                'default': '',
                'is_indexed': 0,
            },
        },
    'sn': {
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
                'is_indexed': 0,
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
    'members': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles': 'Manager',
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
    'members': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles': 'Manager',
            },
        },
    'subgroups': {
        'type': 'CPS String List Field',
        'data': {
                'default': '',
                'is_indexed': 0,
                'acl_write_roles_str': 'Manager',
                'acl_write_expression_str':
                    'dir/hasSubGroupsSupport'
            },
        },
    }

#########################################################

schemas = {
    'members': members_schema,
    'members_search': members_search_schema,
    'roles': roles_schema,
    'groups': groups_schema,
    }

cschemas = context.getCustomDirectorySchemas()
schemas.update(cschemas)

return schemas
