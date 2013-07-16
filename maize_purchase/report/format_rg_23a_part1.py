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

from openerp import tools
from openerp.osv import fields, osv

class format_rg(osv.osv):
    _name = 'format.rg'
    _auto = False
    
    _columns = {
        'date': fields.date('Date'),
        'department_id': fields.many2one('stock.location', 'Description of Inputs Received'),
        'product_qty': fields.float('Quantity Received'),
        'product_uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'partner_id': fields.many2one('res.partner', 'Name and Address of the manufacturer importer stock yard from whom the inputs received'),
        'city': fields.char('Range and Division/Custom House from whose jurisdiction the inputs received', size=32),
        'product_qty_1': fields.float('LT'),
        'product_qty_2': fields.float('LT'),
    }
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'format_rg')
        cr.execute("""
            create or replace view format_rg as (
                select
                sm.id, 
                sm.date as date, 
                sm.department_id as department_id, 
                sm.product_qty as product_qty, 
                sm.product_uom as product_uom_id, 
                sm.partner_id as partner_id, 
                rp.city as city, 
                sm.product_qty as product_qty_1, 
                sm.product_qty as product_qty_2
                from stock_move sm 
                left join res_partner rp on (sm.partner_id = rp.id)
                left join stock_picking sp on (sm.picking_id = sp.id)
                where sm.state = 'done' and sp.type = 'receipt'
            )
        """)
        
format_rg()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: