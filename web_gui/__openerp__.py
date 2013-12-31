{
    "name" : "Web GUI Improvement",
    "category": "Hidden",
    "version" : '1.0',
    "author" : 'OpenERP SA',
    "description":
        """
OpenERP Web GUI Improvement
===========================

**Warning: First Install web_keyboard_shortcut**

- After installing this module search view and main menu become static.
- And also add some functions used in Keyboard shortcuts.
        """,
    "version" : "2.0",
    "depends" : ["web"],
    "js": ["static/src/js/tasks.js"],
    "css": ["static/src/css/tasks.css"],
    'qweb' : ["static/src/xml/*.xml"],
    'installable': True,
    'auto_install': False,
}

