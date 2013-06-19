{
    'name': 'Attachment Size Limit',
    'category': 'Hidden',
    'description': """
Attachment Configuration
========================

* **Company Configuration you can control this three things.**

  * Maximum files allowed to upload per record.
  * Maximum size of file that can be uploaded.
  * Block User.
""",
    'depends': ['web','base','document'],
    'js': [
        'static/src/js/attachment_size_limit.js',
    ],
    'data': [
        'res_company_view.xml',
           ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
