{
    "name" : "Filter Tabs",
    "category": "Hidden",
    "description":
        """
View Filter As a Tab
====================

- Converts custom fields in to tabs

        """,
    "depends" : ["base"],
    "js": ["static/src/js/view_tabs.js"],
    'qweb' : ['static/src/xml/*.xml'],
    'css' : ['static/src/css/tabs.css'],
    'installable': True,
    'auto_install': False,
}

