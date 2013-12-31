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
    'name' : 'Serial Number Tracking',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'sequence': 120,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Tracking parts with serial in warehouse',
    'description' : """
Track products with serial numbers on every transactions
============================================================
With the use of this module you can track the current location of the product with serial numbers.

When the products are moved from one location to another location, the system will automatically identify the current location of the product based on last movement of the product. So you can get the last location where the products are moved.
""",
    'depends' : ['l10n_in_base', 'stock'],
    'data' : [
    ],
    'update_xml' : [
        'stock_serial_tracking_view.xml',
    ],

    'demo': [],

    'installable' : True,
    'application' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
