{
    'name': 'Web Report Small',
    'category': 'Hidden',
    'description': """
OpenERP Web Report Small change.
==========================

        """,
    'version': '2.0',
    'depends':['web'],
    'js': ['static/src/js/*.js'],
    'css': ['static/src/css/*.css'],
    'qweb': ['static/src/xml/*.xml'],
    'auto_install': False,
}
