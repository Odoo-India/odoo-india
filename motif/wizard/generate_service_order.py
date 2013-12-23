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
        warehouse_ids = warehouse_obj.search(cr, uid, [('company_id', '=', data.production_id.company_id.id)], context=context)
        name = seq_obj.get(cr, uid, 'purchase.order')
        if not warehouse_ids:
            raise osv.except_osv(_('Warehouse not found!'), _('Atleast define one warehouse for company "%s"!') % (data.production_id.company_id.name,))
        location_id = warehouse_obj.browse(cr, uid, warehouse_ids[0],context=context).lot_stock_id.id
        supplier = data.service_supplier_id
        origin = data.production_id and data.production_id.name or ''
        return {
                'name': name,
                'origin': origin,
                'partner_ref':'Service Order',
                'partner_id': supplier.id,
                'service_order':True,
                'workorder_id': data.id,
                'location_id': location_id,
                'warehouse_id': warehouse_ids and warehouse_ids[0] or False,
                'pricelist_id': supplier.property_product_pricelist_purchase.id,
                'date_order': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': data.production_id.company_id.id,
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
                'name': data.service_description or '',
                'product_qty': 1.0,  # Default 1 qty
                'product_uom': 1,
                'price_unit': 1.0,
                'date_planned': time.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'order_id':po_id
                }
    

    def create_service_order(self, cr, uid, ids, context=None):
        """
        -Process
            -Check for define supplier on service product?
            -Generate Purchase(Service Order)
        """
        context = context or {}
        wrkorder_obj = self.pool.get('mrp.production.workcenter.line')
        purchase_obj = self.pool.get('purchase.order')
        production_obj = self.pool.get('mrp.production')
        purchase_line_obj = self.pool.get('purchase.order.line')
        wrkorder_id = context and context.get('active_id') or False
        if not wrkorder_id:
            return {}
        data = wrkorder_obj.browse(cr, uid, wrkorder_id, context=context)
        # Create PO
        po_id = purchase_obj.create(cr, uid, self._create_po_vals(cr, uid, data, context=context), context=context)
        # Create PO Lines
        purchase_line_obj.create(cr, uid, self._create_po_line_vals(cr, uid, data, po_id, context=context), context=context)
        wrkorder_obj.modify_production_order_state(cr, uid, [wrkorder_id], 'start')
        data.write({'state':'startworking', 'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),'po_order_id': po_id})
        return True

generate_service_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
