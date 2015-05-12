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
    'name': 'Dealer Price on Invoice (Unsupported)',
    'version': '1.0',
    'category': 'Indian Localization',
    'summary': 'Dealer Price, Compute discount for Dealers on Invoice',
    'description': """Dealer Price on Invoice
=============================================
With the use of this module you can define dealer specific price with the use of dealer's pricelist. On the Invoice you can select the dealer and the relevant pricelist so from the invoice you can get the dealer price amount along with the customer price amount.

This module was developed by TinyERP Private Limited (OpenERP India), not supported under any contracts by OpenERP SA or TinyERP.
""",
    'author': 'OpenERP SA',
    'website': 'http://www.openerp.com',
    'images': [],
    'depends': ['l10n_in_base', 'product_container', 'account'],
    'data': [
        'l10n_in_dealer_discount_invoice.xml'
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
