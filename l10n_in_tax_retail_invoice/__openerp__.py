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
    'name': 'Tax / Retail Invoice',
    'version': '1.0',
    'category': 'Indian Localization',
    'description': """
Indian Localization Module to have feature as listed below.
=========================================================
Created Menus
-------------
    - Settings/Configuration/Indian Localization Defined
Reports
-------
    - Invoices (Default)
    - Petty Cash Voucher
    - Purchase Order
    - Quotation / Order
    - Sale Order with Taxes
    - Tax/Retail Invoice
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['sale_stock', 'delivery', 'account_tax_fix', 'sale_order_dates'],
    'data': [
        'l10n_in_tax_retail_invoice_installer.xml', 
        'report/tax_invoice.xml',
        'report/purchase_order.xml',
        'report/sale_order_tax.xml',
        'report/quotation.xml',
        'report/account_report.xml',
        'report/petty_cash_voucher.xml',
        'l10n_in_tax_retail_invoice_view.xml',
        'res_config_view.xml',
    ],
    'test':[
        'test/purchase_order.yml',
        'test/sale_order.yml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
