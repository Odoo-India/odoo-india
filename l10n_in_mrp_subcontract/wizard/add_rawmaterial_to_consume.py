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
import time

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class add_rawmaterial_to_consume(osv.osv_memory):
    _name = "add.rawmaterial.to.consume"
    _description = "Add Raw Material for Consume"

    def default_get(self, cr, uid, fields, context):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        workorder_id = context and context.get('active_id', False) or False
        finish_move_id = context and context.get('finish_move_id', False) or False
        res = super(add_rawmaterial_to_consume, self).default_get(cr, uid, fields, context=context)

        if 'workorder_id' in fields:
            res.update({'workorder_id': workorder_id})
        if 'finish_move_id' in fields:
            res.update({'finish_move_id': finish_move_id})
        return res

    _columns = {
        'finish_move_id': fields.many2one('stock.move', 'Move'),
        'workorder_id':fields.many2one('mrp.production.workcenter.line', 'WorkOrder'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'uom_id': fields.many2one('product.uom', 'Unit Of Measure', readonly=True),
        'qty_to_consume': fields.float('Quantity To Consume', digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, context=None):
        product = self.pool.get('product.product').browse(cr, uid, product_id)
        return {'value':{'uom_id':product.uom_id.id}}

    def _check_validation_consume_qty(self, cr, uid, qty_to_consume, product_stock):
        """
        - Process
            - Warning raise, if consume_qty > total qty or consume_qty  < 0
        """
        if qty_to_consume <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of consume qty(%s)'%(qty_to_consume)))
        if qty_to_consume > product_stock:
            raise osv.except_osv(_('Consumed Qty over the limit!'), _('Consume Qty(%s) greater then Available Qty(%s)' % (qty_to_consume, product_stock)))
        return True

    def _make_consume_line(self, cr, uid, product, qty_to_consume, finish_move_id, workorder, context=None):
        stock_move = self.pool.get('stock.move')
        production = workorder.production_id
        destination_location_id = product.property_stock_production.id
        source_location_id = production.location_src_id.id
        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'product_id': product.id,
            'product_qty': qty_to_consume,
            'product_uom': product.uom_id.id,
            'product_uos_qty': qty_to_consume,
            'product_uos': product.uom_id.id,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'move_dest_id': finish_move_id,
            'state': 'waiting',
            'company_id': production.company_id.id,
            #True means its consumed dynamically on production order.
            'extra_consumed':True
        })
        production.write({'move_lines': [(4, move_id)]}, context=context)
        return move_id

    def add_consume_qty(self, cr, uid, ids, context=None):
        """
        - Process
            -check validation of add materials qty,
            -create consume line in production order,
            -process and consumed that line
            -create new process line in work-order then consume it
        - Return
            -True
        """
        context = context or {}
        production_obj = self.pool.get('mrp.production')
        process_move = self.pool.get('stock.moves.workorder')
        move_obj =  self.pool.get('stock.move')

        wizard_rec = self.browse(cr, uid, ids[0])
        finish_move_id = wizard_rec.finish_move_id and wizard_rec.finish_move_id.id or False
        workorder = wizard_rec.workorder_id 
        product = wizard_rec.product_id
        qty_to_consume = wizard_rec.qty_to_consume
        product_stock = wizard_rec.product_id.qty_available

        self._check_validation_consume_qty(cr, uid, qty_to_consume, product_stock)
        #create move
        move_id = self._make_consume_line(cr, uid, product, qty_to_consume, finish_move_id, workorder, context=context)
        #Consume move
        move_id and move_obj.action_consume(cr, uid, [move_id], qty_to_consume, context=context)
        move = move_obj.browse(cr, uid, move_id)
        res = production_obj._create_process_dict(cr, uid, move, workorder.id)
        res.update({
                    'state':'consumed',
                    'start_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'accepted_qty': qty_to_consume,
                    })
        process_move.create(cr, uid, res, context=context)
        return True

add_rawmaterial_to_consume()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: