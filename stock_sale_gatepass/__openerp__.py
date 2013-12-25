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
    'name' : 'Sales Delivery Gatepass',
    'version' : '0.1',
    'author' : 'OpenERP S.A.',
    'sequence': 110,
    'category': 'Warehouse Management',
    'website' : 'http://www.openerp.com',
    'summary' : 'Delivery Order link on Delivery Gatepass',
    'description' : """
Sale order link on Delivery Gatepass
=====================================
* Linking of Sales order and Delivery order on gatepass which was already created based on sales confirmation
""",
    'depends' : ['l10n_in_base', 'stock', 'stock_gatepass', 'product_container_tracking'],
    'data' : [
    ],
    'update_xml' : [
        'stock_sale_gatepass_view.xml'
    ],

    'demo': [],

    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: