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
    'name' : 'Repair\'s Gatepass',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Indent Approval link on Repair\'s Gatepass',
    'description' : """
Indent Approval Link on Repair's Gate Pass
=============================================
This module allows you to send products in repairing indent using gate pass and also keeps track of the incoming shipment of repaired products coming back from the supplier who has sent repaired product.

How it works?
********************
Creating Repairing Indent
---------------------------
When you want to send a Laptop out for repairing you will create a repairing indent and select Laptop as product to be sent for repairing and the service to repair the Laptop.

Deliver through Gate Pass
---------------------------
After indent is approved, a returnable gate pass is created for Laptop. The gate keeper can confirm the gate pass and process the delivery of Laptop to be send to supplier for repairing.

Receive through Gate Pass
---------------------------
The incoming shipment for Laptop is also recorded on the same gate pass which is created for the repairing indent. When the Laptop is arrived from the supplier, the gate keeper can process the incoming shipment of Laptop for the same gate pass.

Transfer to the Department
---------------------------
After the repaired Laptop has arrived from supplier, you can issue the products to the department for which the repairing indent was created. Once the internal transfer has been done, the indent will be completed and changed to Received status.
""",
    'depends' : ['l10n_in_base', 'stock_indent', 'stock_gatepass'],
    'data' : [
        'stock_indent_gatepass_view.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
