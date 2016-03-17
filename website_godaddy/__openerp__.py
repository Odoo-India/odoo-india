# -*- coding: utf-8 -*-

{
    'name': 'Godaddy',
    'category': 'Website',
    'sequence': 135,
    'summary': 'GodAddy Integration with Odoo',
    'website': 'https://www.odoo.com/page/website-builder',
    'version': '1.0',
    'description': """
        Online Domains Suggestor
        """,
    'depends': ['website_sale'],
    'data': [
        'data/godaddy_data.xml',
        'views/website_godaddy.xml',
        'views/website_godaddy_view.xml',
        #'security/ir.model.access.csv',
    ],
    #'qweb': ['static/src/xml/*.xml'],
    # 'demo': [
    #     'data/event_demo.xml'
    # ],
    'installable': True,
    'application': True,
}
