# -*- coding: utf-8 -*-
{
    'name': "Indent",

    'summary': """Manage and track internal material requests""",

    'description': """
Indent Management
===================
Usually big companies set-up and maintain internal requisition to be raised by Engineer, Plant Managers or Authorised Employees. Using Indent Management you can control the purchase and issue of material to employees within company warehouse.
- Purchase Indents
- Store purchase
- Capital Purchase
- Repairing Indents
- Project Costing
- Valuation
- etc.

Purchase Indents
++++++++++++++++++
When there is a need of specific materials or services, authorized employees or managers will create a Purchase Indent. He can specify required date, whether the indent is for store or capital, the urgency of materials etc. on indent.
While selecting the product, the system will automatically set the procure method based on the quantity on hand for the product. Once the indent is approved, an internal move has been generated. A purchase order will also be generated if the products are not in stock and to be purchased.

Repairing Indents
++++++++++++++++++
A store manager or will create a repairing indent when the product is needed to be sent for repairing. In case of repairing indent you will be able to select product to be repaired and service for repairing of the product.
A purchase order is generated for the service taken for the supplier who repairs the product, and an internal move has been created for the product to be moved for repairing.
This module was developed by TinyERP Pvt Ltd (OpenERP India). Not covered under OpenERP / Odoo Maintenance Contract or Business Pack. Contact at india@openerp.com if you are looking for support or customization.
    """,

    'author': "Odoo India",
    'website': "http://www.odoo.co.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'purchase'],

    # always loaded
    'data': [
        'security/roles.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'data/sequence.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}