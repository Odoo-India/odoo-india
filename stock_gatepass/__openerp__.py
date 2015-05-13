# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Gate Pass',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Gate Pass, Delivery Orders, Returnable Incoming Shipments',
    'description' : """
Gate Pass
=============
Useful to manage documents that allows gate keeper to pass the outgoing materials, products, etc. and keeps track of returning items.

Manage Returnable/Non-Returnable Gate Pass
++++++++++++++++++++++++++++++++++++++++++++
By selecting proper type on gate pass you can manage returnable or non-returnable products. Its reflected on gate pass created with this type, so you can easily find and manage different types of gate pass.

Once you confirm the gate pass, Delivery Order is automatically created for the products selected on the gate pass. Incoming shipment is also created automatically in case of returnable gate pass, once you validate the gate pass.

Access Delivery Orders and Incoming Shipments easily
+++++++++++++++++++++++++++++++++++++++++++++++++++++
Delivery Orders and Incoming Shipments are linked to gate pass. You can navigate to delivery order and incoming shipment from the buttons on gate pass.

Gate Pass Receipt
+++++++++++++++++++
The report to print the details of gate pass with products and shipping details.

This module was developed by TinyERP Pvt Ltd (OpenERP India). Not covered under OpenERP / Odoo Maintenance Contract or Business Pack. Contact at india@openerp.com if you are looking for support or customization.
""",
    'depends' : ['l10n_in_base', 'stock'],
    'data' : [
        'security/ir.model.access.csv',
        'stock_gatepass_view.xml',
        'stock_gatepass_workflow.xml',
        'stock_gatepass_sequence.xml',
        'stock_gatepass_data.xml',
        'stock_gatepass_report.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
