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
from openerp import netsvc

class indent_indent(osv.Model):
    _name = 'indent.indent'
    _description = 'Indent'

    _columns = {
        'name': fields.char('Name', size=256, required=True),
        'indent_date': fields.date('Indent Date', required=True),
        'required_date': fields.date('Required Date', required=True),
        'indentor_id': fields.many2one('res.users','Indentor', required=True),
        'department_id': fields.many2one('indent.department', 'Department', required=True),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', ondelete="cascade", required=True),
        'requirement': fields.selection([('ordinary','Ordinary'), ('urgent','Urgent')],'Requirement', required=True),
        'type': fields.selection([('new','New'), ('existing','Existing')],'Indent Type', required=True),
        'product_lines': fields.one2many('indent.product.lines', 'indent_id', 'Products'),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'description': fields.text('Description'),
        'company_id': fields.many2one('res.company', 'Company'),
        'state':fields.selection([('draft','Draft'), ('confirm','Confirm'), ('waiting_approval','Waiting For Approval'), ('approved','Approved'), ('waiting_product','Waiting For Products'), ('done','Done'), ('cancel','Cancel')], 'State', readonly=True)
    }
    _defaults = {
        'state': 'draft',
        'name': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'indent.indent'),
        'indent_date': fields.date.context_today,
        'required_date': fields.date.context_today,
        'indentor_id': lambda self, cr, uid, context: uid,
        'requirement': 'ordinary',
        'type': 'new'
    }

    def action_picking_create(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking_id = False
        indent = self.browse(cr, uid, ids[0], context=context)
        if indent.product_lines:
            picking_id = self._create_pickings_and_procurements(cr, uid, indent, indent.product_lines, None, context=context)
        self.write(cr, uid, ids, {'picking_id': picking_id, 'state' : 'waiting_product'}, context=context)
        return picking_id

    def action_receive_products(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display internal move of given indent ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        picking_id = self.browse(cr, uid, ids[0], context=context).picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        result = {
            'name': _('Internal Moves'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': res and res[1] or False,
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': picking_id,
        }
        return result

    def _default_location_source(self, cr, uid, context=None):
        location_model, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
        return location_id

    def _prepare_indent_line_move(self, cr, uid, indent, line, picking_id, date_planned, context=None):
        location_id = self._default_location_source(cr, uid, context=context)
        res = {
            'name': line.name,
            'picking_id': picking_id,
            'product_id': line.product_id.id,
            'date': date_planned,
            'date_expected': date_planned,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty) or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': location_id,
            'location_dest_id': location_id,
            'state': 'draft',
            'price_unit': line.product_id.standard_price or 0.0
        }
        if indent.company_id:
            res = dict(res, company_id = indent.company_id.id)
        return res

    def _prepare_indent_picking(self, cr, uid, indent, context=None):
        pick_name = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking')
        res = {
            'name': pick_name,
            'origin': indent.name,
            'date': indent.indent_date,
            'type': 'internal',
        }
        if indent.company_id:
            res = dict(res, company_id = indent.company_id.id)
        return res

    def _prepare_indent_line_procurement(self, cr, uid, indent, line, move_id, date_planned, context=None):
        location_id = self._default_location_source(cr, uid, context=context)
        res = {
            'name': line.name,
            'origin': indent.name,
            'date_planned': date_planned,
            'product_id': line.product_id.id,
            'product_qty': line.product_uom_qty,
            'product_uom': line.product_uom.id,
            'product_uos_qty': (line.product_uos and line.product_uos_qty)\
                    or line.product_uom_qty,
            'product_uos': (line.product_uos and line.product_uos.id)\
                    or line.product_uom.id,
            'location_id': location_id,
            'procure_method': line.type,
            'move_id': move_id,
            'note': line.name,
        }
        if indent.company_id:
            res = dict(res, company_id = indent.company_id.id)
        return res

#    def _get_date_planned(self, cr, uid, order, line, start_date, context=None):
#        date_planned = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(days=line.delay or 0.0)
#        date_planned = (date_planned - timedelta(days=order.company_id.security_lead)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
#        return date_planned

    def _create_pickings_and_procurements(self, cr, uid, indent, product_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in product_lines:
            date_planned = indent.indent_date
#            date_planned = self._get_date_planned(cr, uid, order, line, order.date_order, context=context)

            if line.product_id:
                if line.product_id.type in ('product', 'consu'):
                    if not picking_id:
                        picking_id = picking_obj.create(cr, uid, self._prepare_indent_picking(cr, uid, indent, context=context))
                    move_id = move_obj.create(cr, uid, self._prepare_indent_line_move(cr, uid, indent, line, picking_id, date_planned, context=context), context=context)
                else:
                    # a service has no stock move
                    move_id = False
                proc_id = procurement_obj.create(cr, uid, self._prepare_indent_line_procurement(cr, uid, indent, line, move_id, date_planned, context=context))
                proc_ids.append(proc_id)

        wf_service = netsvc.LocalService("workflow")
        if picking_id:
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
        for proc_id in proc_ids:
            wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)

        return picking_id

    def indent_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'draft'}, context=context)
        return True

    def indent_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'confirm'}, context=context)
        return True

    def indent_validate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'waiting'}, context=context)
        return True

    def indent_approve(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'inprogress'}, context=context)
        return True

    def indent_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state' : 'done'}, context=context)
        return True

indent_indent()

class indent_product_lines(osv.Model):
    _name = 'indent.product.lines'
    _description = 'Indent Product Lines'

    _columns = {
        'indent_id': fields.many2one('indent.indent', 'Indent', required=True, ondelete='cascade'),
        'name': fields.text('Description', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'type': fields.selection([('make_to_stock', 'from stock'), ('make_to_order', 'on order')], 'Procurement Method', required=True,
         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'qty_available': fields.float('Stock'),
        'name': fields.text('Purpose', required=True),
        'specification': fields.text('Specification'),
    }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
        'product_uom' : _get_uom_id,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'type': 'make_to_stock',
    }

    def product_id_change(self, cr, uid, ids, product, qty=0, uom=False, qty_uos=0, uos=False, name='', date_order=False):
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')

        if not product:
            return {'value': {'product_uos_qty': qty}, 'domain': {'product_uom': [], 'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        warning_msgs = {}
        product_obj = product_obj.browse(cr, uid, product)

        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False

        result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id])[0][1]
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty

        if not uom2:
            uom2 = product_obj.uom_id

        result['type'] = product_obj.procure_method
        result['stock_real'] = product_obj.qty_available
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'), 'message' : warning_msgs
                    }
        return {'value': result, 'domain': domain, 'warning': warning}

    def product_uom_change(self, cr, uid, ids, product, qty=0, uom=False, qty_uos=0, uos=False, name='', date_order=False):
        if not uom:
            return {'value': {'product_uom' : uom or False}}
        return self.product_id_change(cr, uid, ids, product, qty=qty, uom=uom, qty_uos=qty_uos, uos=uos, name=name, date_order=date_order)

indent_product_lines()

class indent_department(osv.Model):
    _name = 'indent.department'
    _description = 'Department'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
    }

indent_department()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
