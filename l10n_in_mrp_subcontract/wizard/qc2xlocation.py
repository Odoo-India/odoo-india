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
import netsvc

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class qc2xlocation(osv.osv_memory):
    _name = "qc2xlocation"
    _description = "QC to X Location"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        context = context or {}
        move_obj = self.pool.get('stock.move')
        to_qc_qty = context and context.get('to_qc_qty', 0.0) or 0.0
        product_id = context and context.get('product_id', False) or False
        move_id = context and context.get('active_id',False) or False
        returned_qty = 0.0
        if move_id:
            move = move_obj.browse(cr, uid, move_id)
            if move.picking_id:
                return_history = self.get_return_history(cr, uid, move.picking_id.id, context)
                returned_qty = return_history.get(move_id, 0)
                to_qc_qty = to_qc_qty - returned_qty
        res = {}
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'to_qc_qty' in fields:
            res.update({'to_qc_qty': to_qc_qty})
        if 'returned_qty' in fields:
            res.update({'returned_qty': returned_qty})
            
        return res

    def get_return_history(self, cr, uid, pick_id, context=None):
        """ 
         Get  return_history.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param pick_id: Picking id
         @param context: A standard dictionary
         @return: A dictionary which of values.
        """
        pick_obj = self.pool.get('stock.picking')
        pick = pick_obj.browse(cr, uid, pick_id, context=context)
        return_history = {}
        for m  in pick.move_lines:
            if m.state == 'done':
                return_history[m.id] = 0
                for rec in m.move_history_ids2:
                    # only take into account 'product return' moves, ignoring any other
                    # kind of upstream moves, such as internal procurements, etc.
                    # a valid return move will be the exact opposite of ours:
                    #     (src location, dest location) <=> (dest location, src location))
                    if rec.location_dest_id.id == m.location_id.id \
                        and rec.location_id.id == m.location_dest_id.id:
                        return_history[m.id] += (rec.product_qty * rec.product_uom.factor)
        return return_history

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'to_qc_qty': fields.float('In QC Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'returned_qty': fields.float('Return Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'process_qty': fields.float('Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
    }


    def _prepare_picking(self, cr, uid, prduction, process_mv, context=None):
        """
        -Process
            --create internal picking dictionary
        - Return 
            - dictionary
        """
        res_company = self.pool.get('res.company')
        return {
                    'name': process_mv.name,
                    'origin': (process_mv.po_order_id.name +':'+ prduction.name) or '',
                    'type': 'internal',
                    'note': prduction.location_src_id.name +' >> '+ prduction.product_id.property_stock_production.name,
                    'move_type': 'direct',
                    'company_id': res_company._company_default_get(cr, uid, 'stock.company', context=context),
                    'partner_id': process_mv.service_supplier_id.id,
                    'invoice_state': 'none',
                    'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    'purchase_id':process_mv.po_order_id.id
                }

    def _prepare_move(self, cr, uid, prduction, process_mv, accepted_qty, new_picking_id):
        """
        -Process
            --create internal move dictionary
        - Return 
            - dictionary
        """
        location_id = prduction.location_src_id.id
        dest_id = prduction.product_id.property_stock_production.id
        return {
            'name': prduction.location_src_id.name +' >> '+ prduction.product_id.property_stock_production.name,
            'picking_id': new_picking_id,
            'product_id': process_mv.product_id.id,
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'product_qty': accepted_qty,
            'product_uom': process_mv.product_id.uom_id.id,
            'product_uos_qty': accepted_qty,
            'product_uos': process_mv.product_id.uom_id.id,
            'location_id': location_id,
            'location_dest_id': dest_id,
            'tracking_id': False,
            'state': 'draft',
            #'state': 'waiting',
            'company_id': prduction.company_id.id,
            'price_unit': process_mv.product_id.standard_price or 0.0
        }


    def _check_validation_process_qty(self, cr, uid, to_qc_qty, process_qty, context=None):
        """
        - Process
            - Warning raise, if process qty > In qc qty or process qty < 0,
        """
        context = context or {}
        if process_qty <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of Approve Quantity (%s)' % (process_qty)))
        if process_qty > to_qc_qty:
            raise osv.except_osv(_('Approve Quantity over the limit!'), _('Approve Quantity(%s) greater then In QC Quantity(%s)' % (process_qty, to_qc_qty)))
        return True

    def to_process_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for Accepted qty
            - create copy move.
            - call action_done() to transfer po destination location
        """
        context = context or {}
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        move_id = context.get('active_id',False)
        wizard_rec = self.browse(cr, uid, ids[0])
        move_data = move_obj.browse(cr, uid, move_id)
        to_qc_qty = wizard_rec.to_qc_qty
        process_qty = wizard_rec.process_qty
        returned_qty = wizard_rec.returned_qty

        self._check_validation_process_qty(cr, uid, to_qc_qty, process_qty, context=context)
        default_val = {
                        'product_qty': process_qty,
                        'product_uos_qty': process_qty,
                        'location_id':move_data.location_dest_id.id,
                        'location_dest_id':move_data.picking_id.purchase_id.location_id.id,
                        'state': 'draft',
                        'qc_completed':False,
                        'qc_approved':True,
                        'picking_id':False
                    }
        #create copy move#Done#write into store move
        current_move = move_obj.copy(cr, uid, move_id, default_val, context=context)
        move_obj.action_done(cr, uid, [current_move], context=context)
        pick_obj.write(cr, uid, move_data.picking_id.id, {'move_lines_qc2store': [(4, current_move)]}, context=context)
        #update QC quantity to old move line
        #qc_completed== True if total == QC 
        total_qc_qty = move_data.qc_ok_qty + process_qty
        dict_to = {'qc_ok_qty': total_qc_qty}
        if move_data.product_qty == total_qc_qty + returned_qty:
            dict_to.update({'qc_completed':True})
        move_data.write(dict_to)
        return True

qc2xlocation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
