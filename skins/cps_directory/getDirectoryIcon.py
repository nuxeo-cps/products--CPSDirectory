##parameters=dirname
#
"""
Returns the icon corresponding to directory name.
If no icon exists for the given directory name 
UserFolder_icon.png is returned.
"""
#$Id$

dir_icons = {'groups'  : 'group_directory.png',
             'members' : 'member_directory.png', 
             'roles'   : 'roles_directory.png',
            }

return dir_icons.get(dirname, 'UserFolder_icon.png')