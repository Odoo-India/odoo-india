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
    'name': 'Packing Cost Transfer to Invoice',
    'version': '1.0',
    'category': 'Indian Localization',
    'summary':'Packing Cost transfer to Invoice from Warehouse',
    'description': """
Transfer packing cost to Invoice from Warehouse
====================================================
With the use of this module the packing cost will be transferred from Sales order to Invoice via warehouse.

If you want to sell goods to be delivered in a container (package), You can add extra packaging cost directly then it will calculate container product's sale price as packaging price and calculate final price on the sales order.

When the invoice is created for the sales order, the amount is getting transferred to the invoice.
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['l10n_in_base', 'l10n_in_sales_packing', 'sale_stock'],
    'data': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
