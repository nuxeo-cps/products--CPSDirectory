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
        },
    }

###########################################################

directories = {
    'members': members_directory,
    }

return directories
