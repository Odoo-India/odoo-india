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
    'name': 'Dealer Price on Sales',
    'version': '1.0',
    'category': 'Indian Localization',
    'summary': 'Dealer Price, Discount for Dealers on Sales',
    'description': """
Dealer Price, Discount for Dealers on Sales
===============================================
With the use of this module you can define dealer specific price on Quotations/Sales orders with the use of dealer's pricelist. On the Quotations/Sales orders you can select the dealer and the relevant pricelist so from the sales orders you can get the dealer price amount along with the customer price amount.

This module was developed by TinyERP Pvt Ltd (OpenERP India). Not covered under OpenERP / Odoo Maintenance Contract or Business Pack. Contact at india@openerp.com if you are looking for support or customization.
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['l10n_in_base', 'l10n_in_dealer_discount_invoice', 'l10n_in_sale_invoice_reverse', 'sale_stock'],
    'data': [
        'l10n_in_dealers_discount.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
