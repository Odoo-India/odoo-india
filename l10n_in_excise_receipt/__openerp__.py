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
    'name' : 'Excisable Receipt',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 120,
    'category': 'Indian Localization',
    'website' : 'http://www.openerp.com',
    'description' : """
Excise Duties on the Goods Receipt
====================================
This module allows you to manage Goods Receipt and excise duties on the goods receipts and supplier invoices.

Key Features
++++++++++++++
* Goods Receipts
* Manage Import duties, Excise, Cess etc. on goods receipt
* Manage Packaging & Forwarding, Freight, Excise, Insurance, Cess, etc. on purchase orders
* Forward all taxes and charges from purchase orders to invoices via goods receipt
* Cash, Non-Cash, Free of charge inwards

How it works?
++++++++++++++
When the indent is approved for a need of specific materials, a purchase order will be generated and Packaging & Forwarding, Freight, Taxes, Excise etc. information can be mentioned on the purchase order if any.

Once the purchase order is confirmed and incoming shipment is received, OpenERP will generate goods receipt instead of moving goods directly in stock. Goods receipt will contain all the details of packaging, excise etc. from the purchase order.

When the invoice is created from goods receipt, the accounting entries also got reflected by different charges and taxes. Thus it will be easy for the accountants to get values of excise, cess, other taxes.
""",
    'depends' : ['l10n_in_base', 'stock_indent', 'l10n_in_purchase', 'l10n_in_account_tax'],

    'data' : [
        'receipt_sequence.xml',
    ],

    'update_xml' : [
        'l10n_in_excise_receipt_view.xml',
    ],

    'demo': [
        'dispatch_mode_demo.xml'
    ],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
