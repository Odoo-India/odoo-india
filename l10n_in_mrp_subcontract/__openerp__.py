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
    'name': 'Indian Manufacturing Subcontract',
    'version': '1.0',
    'category' : 'Indian Localization',
    'description':'''
		Extend the flow of manufacturing process
    ''',
    'author': 'OpenERP SA',
    'depends': ['base','mrp_operations','mrp_jit','sale_stock'],
    'data': ['mrp_view.xml','purchase_view.xml','product_view.xml', 'stock_view.xml','wizard/process_qty_to_reject_view.xml','wizard/process_qty_to_finished_view.xml',
             'wizard/all_in_once_qty_to_finished_view.xml','wizard/all_in_once_qty_to_cancelled_view.xml',
             'wizard/reallocate_rejected_move_view.xml','wizard/generate_service_order_view.xml',
             'wizard/qty_to_consume_view.xml','wizard/add_rawmaterial_to_consume_view.xml',
             'wizard/consignment_variation_po_view.xml'
             ],
    'demo': [],
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
