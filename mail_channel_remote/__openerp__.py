# -*- coding: utf-8 -*-

{
    'name': 'Remote Message',
    'category': 'Social Network',
    'summary': 'Read the message in Odoo Messaging System.',
    'description': """
Integrate to Odoo Messaging System.
============================================

Main Features
-------------
Help : https://docs.google.com/document/d/1BDZQy2xy6_rVRk9B7_SRmEc0H23bw8n1eSybv_RCfIQ/edit?usp=sharing
""",
    'license': 'OEEL-1',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/mail_remote_command_views.xml',
        'views/mail_remote_command_template.xml',
    ],
    'qweb': [
        'static/src/xml/composer.xml',
    ],
}
