{
    "name" : "Group Expand Buttons",
    "category": "Hidden",
    "version" : '1.0',
    "author" : 'OpenERP SA',
    "description":
        """
Group Expand Buttons
====================

- This module enables expand and collapse in List Group By
        """,
    "depends" : ["web"],
    "js": ["static/src/js/web_group_expand.js"],
     'qweb' : ["static/src/xml/expand_buttons.xml"],
     'css' : ["static/src/css/expand_buttons.css"],
    'installable': True,
    'auto_install': False,
}

