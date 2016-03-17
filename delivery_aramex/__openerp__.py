# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Aramex Shipping",
    'description': "Send your shippings through Aramex and track them online",
    'author': "Odoo SA",
    'website': "https://www.odoo.com",
    'category': 'Technical Settings',
    'version': '1.0',
    'depends': ['delivery', 'mail'],
    'data': [
        'data/delivery_aramex.xml',
        'views/delivery_aramex.xml',
    ],
    'demo': [
        'data/delivery_aramex_demo.xml'
    ]
}
