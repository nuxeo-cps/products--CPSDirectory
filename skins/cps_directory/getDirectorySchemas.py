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
                'default_expr': 'string:',
            },
        },
    'password': {
        'type': 'CPS Password Field',
        'data': {
                'default_expr': 'string:',
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'confirm': {
        'type': 'CPS Password Field',
        'data': {
            'default_expr': 'string:',
            'read_ignore_storage': 1,
            'write_ignore_storage': 1,
        },
    },
    'roles': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
                'acl_write_roles': 'Manager',
            },
        },
    'groups': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
                'acl_write_roles': 'Manager',
            },
        },
    'givenName': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'sn': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
                'acl_write_roles': 'Manager; Owner',
            },
        },
    'fullname': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
                'acl_write_roles': 'Nobody',
                'read_ignore_storage': 1,
                'read_process_expr': 'python:givenName and sn and (givenName + " " + sn) or id',
                'read_process_dependent_fields': ['givenName', 'sn', 'id'],
                'write_ignore_storage': 1,
            },
        },
    'email': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
                'acl_write_roles': 'Manager; Owner',
            },
        },
    }

members_search_schema = {
    'id': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
            },
        },
    'roles': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
            },
        },
    'groups': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
            },
        },
    'givenName': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
            },
        },
    'sn': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
            },
        },
    'email': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
            },
        },
    }

#########################################################
# roles

roles_schema = {
    'role': {
        'type': 'CPS String Field',
        'data': {
                'default_expr': 'string:',
            },
        },
    'members': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
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
                'default_expr': 'string:',
            },
        },
    'members': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
                'acl_write_roles': 'Manager',
            },
        },
    'subgroups': {
        'type': 'CPS String List Field',
        'data': {
                'default_expr': 'python:[]',
                'acl_write_roles_str': 'Manager',
                'acl_write_expression_str':
                    'dir/hasSubGroupsSupport'
            },
        },
    }

#########################################################

schemas = {
    'members': members_schema,
    'roles': roles_schema,
    'groups': groups_schema,
    }

cschemas = context.getCustomDirectorySchemas()
schemas.update(cschemas)

return schemas
