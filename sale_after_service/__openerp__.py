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
    'name': 'After Sales Service ',
    'version': '1.0',
    'category': 'Sales',
    'description': """
Managing Service Contracts
=========================================

This Module addding the feature of creation of contract after sales for maintaince of services.
- Add boolean on product form which allow creation of contract for that product from delivery order.
- Create contract from delivery order if delivery order line has serial number.
- Contract from delivery order has reference of sale order and delivery order.

TODO
- Security
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': [
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
