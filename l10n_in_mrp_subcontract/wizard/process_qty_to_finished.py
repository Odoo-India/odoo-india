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

class process_qty_to_finished(osv.osv_memory):
    _name = "process.qty.to.finished"
    _description = "Process Quantity To Accept Wizard"

    def default_get(self, cr, uid, fields, context=None):
        """
        -Process
            -Set default values of 
                -Active_id
                -Product
                -Total Qty
        """
        context = context or {}
        mrp_obj = self.pool.get('mrp.production')
        process_move_id = context and context.get('active_id', False) or False
        total_qty = context and context.get('total_qty', 0.0) or 0.0
        product_id = context and context.get('product_id', False) or False
        process_qty = context and context.get('process_qty', 0.0) or 0.0
        already_accepted_qty = context and context.get('already_accepted_qty', 0.0) or 0.0

        res = super(process_qty_to_finished, self).default_get(cr, uid, fields, context=context)
        next_stage_workorder_id, production_id = False, False
        if process_move_id:
            # return [next route, production_id]
            next_stage = mrp_obj.next_stage_workorder(cr, uid, process_move_id, context=context)
            next_stage_workorder_id = next_stage[0]  # next route
            production_id = next_stage[1]  # production id

        if 'process_move_id' in fields:
            res.update({'process_move_id': process_move_id})
        if 'product_id' in fields:
            res.update({'product_id': product_id})
        if 'total_qty' in fields:
            res.update({'total_qty': total_qty})
        if 'process_qty' in fields:
            res.update({'process_qty': process_qty})
        if 'already_accepted_qty' in fields:
            res.update({'already_accepted_qty': already_accepted_qty})
        if 'accepted_qty' in fields:
            res.update({'accepted_qty': 0.0})
        if 'next_stage_workorder_id' in fields:
            res.update({'next_stage_workorder_id': next_stage_workorder_id})
        if 'production_id' in fields:
            res.update({'production_id': production_id})
        return res

    _columns = {
        'process_move_id':fields.many2one('stock.moves.workorder', 'WorkOrder Move'),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'total_qty': fields.float('Total Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'process_qty': fields.float('Process Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'already_accepted_qty': fields.float('Already Accepted Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True),
        'accepted_qty': fields.float('Accept Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'next_stage_workorder_id':fields.many2one('mrp.production.workcenter.line', 'Next Stage of Work-Order'),
        'production_id':fields.many2one('mrp.production', 'Production'),
    }

    def onchange_workorder_id(self, cr, uid, ids, workorder_id, production_id, context=None):
        """
        -Process
            -to set domain of current production order
        """
        context = context or {}
        workorder_line_obj = self.pool.get('mrp.production.workcenter.line')
        current_wrkorder_id = context and context.get('active_id', False) or False
        where_clause = [('production_id', '=', production_id),('state','!=','cancel')]
        if current_wrkorder_id:
            where_clause.append(('id','!=',current_wrkorder_id))
        workorder_ids = workorder_line_obj.search(cr, uid, where_clause, context=context)
        return {'domain': {'next_stage_workorder_id': [('id', 'in', workorder_ids)]}}

    def _check_for_available_outsource_qty(self, cr, uid, process_move_id, production_location_id, accepted_qty, already_accepted_qty, context=None):
        """
        - Process
            - First check that Purchase order have any shipments?
                if Yes,
                    - find recieved quantity of product at store.
                    - compare with in process qty to process.
                If No
                    - Raise warning, No inword has been taken YET
        """
        context = context or {}
        process_mv_obj = self.pool.get('stock.moves.workorder')
        process_mv = process_mv_obj.browse(cr, uid, process_move_id, context=context)
        if not (process_mv.po_order_id or production_location_id):
            return True

        cr.execute("""
                    SELECT sm.product_id,sum(sm.product_qty) as qty FROM stock_move sm 
                    LEFT JOIN stock_picking sp on (sp.id = sm.picking_id or sp.id = sm.picking_qc_id)
                    WHERE sp.purchase_id = %s
                    AND sm.state = 'done'
                    AND sm.location_dest_id = %s
                    GROUP BY sm.product_id
            """%(process_mv.po_order_id.id, production_location_id,))

        inword_qty = [x['qty'] for x in cr.dictfetchall() if x['product_id'] == process_mv.product_id.id]
        if not inword_qty:
            raise osv.except_osv(_('Warning!'), _('Inword of purchase order(%s) haven"t recieved at production' % (process_mv.po_order_id.name)))

        remain_to_process_qty = inword_qty[0] - already_accepted_qty
        if accepted_qty > remain_to_process_qty:
            raise osv.except_osv(_('Accepted Qty Over The Limit!'), _('You cannot process outsource product(%s) \n\n Outsource Process Qty = %s \n Total Inword Qty = %s \n Remain To Process Qty = %s' % (process_mv.product_id.name, accepted_qty, inword_qty[0], remain_to_process_qty)))
        return True

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

    def _generate_internal_moves_to_production(self, cr, uid, prduction, accepted_qty, process_move_id, raw_material_location_id, context=None):
        """
        -Process
            -create internal picking dictionary
            -create internal move dictionary
                - Source Location : Raw Material Location
                - Destination Location : Production(Finished Product Production Location)
        - Return 
            -True
        """
        context = context or {}
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        process_mv_obj = self.pool.get('stock.moves.workorder')
        process_mv = process_mv_obj.browse(cr, uid, process_move_id, context=context)

        #create internal picking from store to production
        new_picking_id = pick_obj.create(cr, uid, self._prepare_picking(cr, uid, prduction, process_mv, context=context), context=context)
        #create move
        move_obj.create(cr, uid, self._prepare_move(cr, uid, prduction, process_mv, accepted_qty, new_picking_id), context=context)

        #Picking Directly Done
        wf_service.trg_validate(uid, 'stock.picking', new_picking_id, 'button_confirm', cr)
        pick_obj.action_move(cr, uid, [new_picking_id], context)
        wf_service.trg_validate(uid, 'stock.picking', new_picking_id, 'button_done', cr)

        return True


    def _check_validation_finished_qty(self, cr, uid, prduction, total_qty, accepted_qty, already_accepted_qty, process_move_id=False, order_type='in', production_location_id=False, context=None):
        """
        - Process
            - Warning raise, if accepted qty > In process qty or accepted qty < 0,
            - Check Stock of Inword Shipments,
            - create internal picking dictionary,
            - create internal move dictionary,
                - Source Location : Raw Material Location
                - Destination Location : Production(Finished Product Production Location)
        """
        context = context or {}
        if accepted_qty <= 0.0:
            raise osv.except_osv(_('Warning!'), _('Provide proper value of Accepted qty(%s)' % (accepted_qty)))
        if accepted_qty > total_qty:
            raise osv.except_osv(_('Accepted Qty over the limit!'), _('Accepted Qty(%s) greater then In Process Qty(%s)' % (accepted_qty, total_qty)))
        if process_move_id and order_type =='out':
            self._check_for_available_outsource_qty(cr, uid, process_move_id, production_location_id, accepted_qty, already_accepted_qty, context=context)
            #self._generate_internal_moves_to_production(cr, uid, prduction, accepted_qty, process_move_id, raw_material_location_id, context=context)
        return True

    def to_finish_qty(self, cr, uid, ids, context=None):
        """
        - Process
            - Warning raise, Validation check for Accepted qty
            - update according workorder process move
            - create new work-order move and attached to next stage if process goes to finished.
        """
        production_obj = self.pool.get('mrp.production')
        process_move = self.pool.get('stock.moves.workorder')
        wizard_rec = self.browse(cr, uid, ids[0])
        already_accepted_qty = wizard_rec.already_accepted_qty
        accepted_qty = wizard_rec.accepted_qty
        process_qty = wizard_rec.process_qty
        next_workorder_id = wizard_rec.next_stage_workorder_id.id
        process_move_id = wizard_rec.process_move_id.id
        order_type = wizard_rec.process_move_id.order_type or 'in'
        prduction = wizard_rec.production_id
        #raw_material_location_id = wizard_rec.production_id.location_src_id.id
        production_location_id = wizard_rec.production_id.product_id.property_stock_production.id

        self._check_validation_finished_qty(cr, uid, prduction, process_qty, accepted_qty, already_accepted_qty, process_move_id, order_type, production_location_id, context=context)
        updt_prcs_mve = {}
        if process_qty == accepted_qty:
            updt_prcs_mve.update({
                                  'state':'finished',
                                  'accepted_qty': already_accepted_qty + accepted_qty,
                                  'process_qty': process_qty - accepted_qty,
                                  'end_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  })
        else:
            updt_prcs_mve.update({
                                  'accepted_qty': already_accepted_qty + accepted_qty,
                                  'process_qty': process_qty - accepted_qty
                                  })

        # to write old process moves
        wizard_rec.process_move_id.write(updt_prcs_mve)

        # create new process move of next stage if work-order available.
        if next_workorder_id:
            res = production_obj._create_process_dict(cr, uid, wizard_rec.process_move_id.move_id, next_workorder_id)
            res.update({'total_qty':accepted_qty})
            process_move.create(cr, uid, res, context=context)
        else:
            # TODO:Close order if all products have done stage...
            print "process flow goes to done"

        return True

process_qty_to_finished()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
