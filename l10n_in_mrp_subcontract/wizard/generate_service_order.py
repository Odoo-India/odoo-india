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

from openerp.osv import osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class generate_service_order(osv.osv_memory):
    _name = "generate.service.order"
    _description = "Service Order"

    def _create_po_vals(self, cr, uid, data, context=None):
        """
        -Proccess
            -Create dictionary of purchase order
        -Return
            -Dictionary
        """
        seq_obj = self.pool.get('ir.sequence')
        warehouse_obj = self.pool.get('stock.warehouse')
        warehouse_ids = warehouse_obj.search(cr, uid, [('company_id', '=', data.workorder_id.production_id.company_id.id)], context=context)
        name = seq_obj.get(cr, uid, 'purchase.order')
        if not warehouse_ids:
            raise osv.except_osv(_('Warehouse not found!'), _('Atleast define one warehouse for company "%s"!') % (data.workorder_id.production_id.company_id.name,))

        #GO TO QC FIRST, QC -> STORE -> PRODUCTION
        #location_id = warehouse_obj.browse(cr, uid, warehouse_ids[0],context=context).lot_input_id.id

        #SUPPLIER >> PRODUCTION
        location_id = data.workorder_id.production_id.product_id.property_stock_production.id
        supplier = data.service_supplier_id
        origin = data.workorder_id.production_id and data.workorder_id.production_id.name or ''
        return {
                'name': name,
                'origin': origin,
                'partner_ref':'Service Order',
                'partner_id': supplier.id,
                'service_order':True,
                'workorder_id': data.workorder_id.id,
                'location_id': location_id,
                'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                'pricelist_id': supplier.property_product_pricelist_purchase.id,
                'date_order': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': data.workorder_id.production_id.company_id.id,
                'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                'payment_term_id': supplier.property_supplier_payment_term.id or False,
                }

    def _create_po_line_vals(self, cr, uid, data, po_id, context=None):
        """
        -Process
            -Create lines of purchase order
        -Return
            -Dictionary
        """
        context = context or {}
        return {
                'name': data.product_id and data.product_id.name or '',
                'product_id': data.product_id and  data.product_id.id or False,
                'product_qty': data.total_qty,
                'line_qty': data.product_id and (data.total_qty * data.product_id.p_coefficient) or data.total_qty,
                'line_uom_id': data.product_id and (data.product_id.p_uom_id.id or data.product_id.uom_id.id) or 1,
                'product_uom': data.product_id and data.product_id.uom_id.id or 1,
                'price_unit': data.product_id and data.product_id.standard_price or 0.0,
                'date_planned': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'order_id':po_id,
                'process_move_id':data.id
                }

    def _create_delivery_picking(self, cr, uid, data, context=None):
        """
        Process
            -Create Delivery Picking for outsource
        Return
            -Dictionary of picking
        """
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        production = data.workorder_id.production_id
        return {
            'name': pick_name,
            'origin': production.name,
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'type': 'out',
            'state': 'draft',
            'partner_id': data.service_supplier_id.id,
            'note': 'Service Note:',
            'invoice_state': 'none',
            'company_id': production.company_id.id,
            'service_order':True,
            'workorder_id': data.workorder_id.id,
        }

    def _create_delivery_move(self, cr , uid, data, deliver_id, context=None):
        """
        Process
            -Create move for outsource
                From : Production Location
                To : Supplier Location
        Return
            -Dictionary of move
        """
        context = context or {}
        if not data.workorder_id:
            raise osv.except_osv(_('Save Record!'), _('First you save this record!'))
        production = data.workorder_id.production_id

        #Delivery Order Locations
        source_location_id = production.product_id.property_stock_production.id
        dest_location_id = data.service_supplier_id.property_stock_supplier.id
        return {
            'name': 'Service:'+ data.product_id.name,
            'picking_id': deliver_id,
            'product_id': data.product_id.id,
            'date': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'date_expected': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'product_qty': data.total_qty,
            'product_uom': data.product_id.uom_id.id,
            'product_uos_qty': data.total_qty,
            'product_uos': data.product_id.uom_id.id,
            'partner_id': data.service_supplier_id.id,
            'location_id': source_location_id,
            'location_dest_id': dest_location_id,
            'tracking_id': False,
            'state': 'draft',
            'company_id': production.company_id.id,
            'price_unit': data.product_id.standard_price or 0.0
        }

    def create_service_order(self, cr, uid, ids, context=None):
        """
        -Process(Purchase Order + Delivery Order)
            -Check for define supplier on service product?
            -Generate Purchase(Service Order)
        
        """
        context = context or {}
        wrkorder_obj = self.pool.get('mrp.production.workcenter.line')
        pmove_obj = self.pool.get('stock.moves.workorder')
        out_pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        purchase_obj = self.pool.get('purchase.order')
        production_obj = self.pool.get('mrp.production')
        purchase_line_obj = self.pool.get('purchase.order.line')
        process_move_id = context and context.get('active_id') or False
        if not process_move_id:
            return {}
        data = pmove_obj.browse(cr, uid, process_move_id, context=context)
        # Create PO
        po_id = purchase_obj.create(cr, uid, self._create_po_vals(cr, uid, data, context=context), context=context)
        # Create PO Lines
        purchase_line_obj.create(cr, uid, self._create_po_line_vals(cr, uid, data, po_id, context=context), context=context)

        # Create Delivery Order
        delivery_order_id = out_pick_obj.create(cr, uid, self._create_delivery_picking(cr, uid, data, context=context), context=context)
        # Create Move
        move_obj.create(cr, uid, self._create_delivery_move(cr, uid, data, delivery_order_id, context=context), context=context)

        pmove_obj.write(cr, uid, process_move_id, {
                                  'state':'in_progress',
                                  'start_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                  'process_qty':data.total_qty,
                                  'po_order_id':po_id,
                                  'delivery_order_id':delivery_order_id
                                  })
        #Picking Directly Done
        wf_service.trg_validate(uid, 'stock.picking', delivery_order_id, 'button_confirm', cr)
        out_pick_obj.action_move(cr, uid, [delivery_order_id], context)
        wf_service.trg_validate(uid, 'stock.picking', delivery_order_id, 'button_done', cr)

        #Start Work-Order Also.
        wf_service.trg_validate(uid, 'mrp.production.workcenter.line', data.workorder_id.id, 'button_start_working', cr)

#        wrkorder_obj.modify_production_order_state(cr, uid, [wrkorder_id], 'start')
#        data.write({'state':'startworking', 'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),'po_order_id': po_id})
        return True

generate_service_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
