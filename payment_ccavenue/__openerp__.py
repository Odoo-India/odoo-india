# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'CCAvenue Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: CCAvenue Implementation',
    'description': """CCAvenue Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/ccavenue.xml',
        'views/payment_acquirer.xml',
        'data/payment_ccavenue_data.xml',
        'views/payment_ccavenue_template.xml',
    ],
    'license': 'OEEL-1',
}
