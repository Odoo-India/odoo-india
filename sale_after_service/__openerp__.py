# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
    'name': 'After Sales Service Contracts',
    'version': '1.0',
    'category': 'Sales',
    'summary' : 'Manage Service Contracts',
    'description': """
Manage service contract for the products after sales
====================================================== 
This module adds the feature of automatic creation of contracts for maintenance or services after the sales of products.

How it works?
+++++++++++++++
The contract is created from delivery order if delivery order line has serial number and the product has a boolean true for after sales services. A boolean on product for Service after sales, when selected, allows creation of contracts for that product while processing delivery of that product, if proper serial number is selected.

* Adds boolean on product form for after sales service
* If delivery order line has serial number, Creates contract from delivery order
* Created contract has reference of sale order and delivery order to search it easily
* Serial Number also has reference of created contract, if any
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': [
        'l10n_in_base', 
        'sale_stock', 
        'account_analytic_analysis', 
        'crm'
    ],
    'data': [
        'sale_after_service_view.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
