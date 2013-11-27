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
import datetime
import netsvc
from datetime import timedelta

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

SERIES = [
    ('repair', 'Repair'),
    ('purchase', 'Purchase'),
    ('store', 'Store')
]

class stock_location(osv.Model):
    _inherit = 'stock.location'
    _columns = {
        'manager_id': fields.many2one('res.users', 'Manager'),
        'can_request': fields.boolean('Can request for item ?')
    }
stock_location()

class indent_indent(osv.Model):
    _name = 'indent.indent'
    _description = 'Indent'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "id desc"
    
    _track = {
        'state': {
            'indent.mt_indent_waiting_approval': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'waiting_approval',
            'indent.mt_indent_inprogress': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'inprogress',
            'indent.mt_indent_received': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'received',
            'indent.mt_indent_rejected': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'reject'
        },
    }

    def _total_amount(self, cr, uid, ids, name, args, context=None):
        result = {}
        for indent in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in indent.product_lines:
                total += line.price_subtotal
            result[indent.id] = total
        return result

    def _get_product_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('indent.product.lines').browse(cr, uid, ids, context=context):
            result[line.indent_id.id] = True
        return result.keys()

    _columns = {
        'name': fields.char('Indent #', size=256, readonly=True, track_visibility='always'),
        'indent_date': fields.datetime('Indent Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'required_date': fields.datetime('Required Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'indentor_id': fields.many2one('res.users', 'Indentor', required=True, readonly=True, track_visibility='always', states={'draft': [('readonly', False)]}),
        'manager_id': fields.related('department_id', 'manager_id', readonly=True, type='many2one', relation='res.users', string='Department Manager', store=True, states={'draft': [('readonly', False)]}),
        'department_id': fields.many2one('stock.location', 'Department', required=True, readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}, domain=[('can_request','=', True)]),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', ondelete="cascade",readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
        'requirement': fields.selection([('ordinary', 'Ordinary'), ('urgent', 'Urgent')], 'Requirement', readonly=True, required=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
        'type': fields.selection([('new', 'Store'), ('existing', 'Repairing')], 'Type', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}),
        'product_lines': fields.one2many('indent.product.lines', 'indent_id', 'Products', readonly=True, states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]}),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'description': fields.text('Additional Information', readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company', 'Company', readonly=True, states={'draft': [('readonly', False)]}),
        'active': fields.boolean('Active'),
        'item_for': fields.selection([('store', 'Store'), ('capital', 'Capital')], 'Item for', readonly=True, states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(_total_amount, type="float", string='Total',
            store={
                'indent.indent': (lambda self, cr, uid, ids, c={}: ids, ['product_lines'], 20),
                'indent.product.lines': (_get_product_line, ['price_subtotal', 'product_uom_qty', 'indent_id'], 20),
            }),
        'state':fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('waiting_approval', 'Waiting For Approval'), ('inprogress', 'Inprogress'), ('received', 'Received'), ('reject', 'Rejected')], 'State', readonly=True, track_visibility='onchange'),
        'approver_id': fields.many2one('res.users', 'Authority', readonly=True, track_visibility='always', states={'draft': [('readonly', False)]}, help="who have approve or reject indent."),
    }
    
    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    def _get_required_date(self, cr, uid, context=None):
        return datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=7), DEFAULT_SERVER_DATETIME_FORMAT)
    
    def _get_date_planned(self, cr, uid, indent, line, start_date, context=None):
        date_planned = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=line.delay or 0.0)
        return date_planned

    _defaults = {
        'state': 'draft',
        'indent_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'required_date': _get_required_date,
        'indentor_id': lambda self, cr, uid, context: uid,
        'requirement': 'ordinary',
        'type': 'new',
        'department_id':_default_stock_location,
        'item_for':'store',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'indent.indent', context=c),
        'name':"/",
        'active': True,
        'approver_id':False
    }

    def onchange_requirement(self, cr, uid, ids, indent_date, requirement='urgent', context=None):
        vals = {}
        days_delay = 7
        if requirement == 'urgent':
            days_delay = 3
        #TODO: for the moment it will count the next days based on the system time 
        #and not based on the indent_date available on the indent. 
        required_day = datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=days_delay), DEFAULT_SERVER_DATETIME_FORMAT)
        vals.update({'value':{'required_date':required_day}})
        return vals
    
    def _needaction_domain_get(self, cr, uid, context=None):
        return [('state', '=', 'waiting_approval')]

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'name': "/",
            'indent_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'requirement': 'ordinary',
            'picking_id': False,
            'indent_authority_ids': [],
            'state': 'draft',
            'approver_id':False
        })
        return super(indent_indent, self).copy(cr, uid, id, default, context=context)

    def onchange_item(self, cr, uid, ids, item_for=False, context=None):
        result = {}
        if not item_for or item_for == 'store':
            result['analytic_account_id'] = False
        return {'value': result}
    
    def indent_confirm(self, cr, uid, ids, context=None):
        for indent in self.browse(cr, uid, ids, context=context): 
            if not indent.product_lines:
                raise osv.except_osv(_('Warning!'),_('You cannot confirm an indent %s which has no line.' % (indent.name)))
            
            res = {
               'name':self.pool.get('ir.sequence').get(cr, uid, 'stock.indent'),
               'state': 'waiting_approval'
            }
            self.write(cr, uid, ids, res, context=context)

        return True
    
    def _prepare_indent_line_procurement(self, cr, uid, indent, line, move_id, date_planned, context=None):
        warehouse_obj = self.pool.get('stock.warehouse')
        company_id = indent.company_id.id
        warehouse_ids = warehouse_obj.search(cr, uid, [('company_id', '=', company_id)], context=context)
        warehouse_id = warehouse_ids and warehouse_ids[0] or False
        location_id = warehouse_obj.browse(cr, uid, warehouse_id, context=context).lot_input_id.id
        res = {
            'name': line.name,
            'origin': indent.name,
            'indent_id': indent.id,
            'indentor_id': indent.indentor_id.id,
            'department_id': indent.department_id.id,
            'analytic_account_id': indent.analytic_account_id.id,
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
    
    def _prepare_indent_line_move(self, cr, uid, indent, line, picking_id, date_planned, context=None):
        location_id = self._default_stock_location(cr, uid, context=context)
        res = {
            'name': line.name,
            'indent': indent.id,
            'indentor': indent.indentor_id.id,
            'department_id': indent.department_id.id,
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
            'location_dest_id': indent.department_id.id,
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

    def _create_pickings_and_procurements(self, cr, uid, indent, product_lines, picking_id=False, context=None):
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        procurement_obj = self.pool.get('procurement.order')
        proc_ids = []

        for line in product_lines:
            date_planned = self._get_date_planned(cr, uid, indent, line, indent.indent_date, context=context)

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

    def action_picking_create(self, cr, uid, ids, context=None):
        proc_obj = self.pool.get('procurement.order')
        move_obj = self.pool.get('stock.move')
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking_id = False
        indent = self.browse(cr, uid, ids[0], context=context)
        if indent.product_lines:
            picking_id = self._create_pickings_and_procurements(cr, uid, indent, indent.product_lines, None, context=context)
        self.write(cr, uid, ids, {'picking_id': picking_id, 'state' : 'inprogress'}, context=context)
        wf_service = netsvc.LocalService("workflow")

        move_ids = move_obj.search(cr,uid,[('picking_id','=',picking_id)])
        pro_ids = proc_obj.search(cr,uid,[('move_id','in',move_ids)])
        for pro in pro_ids:
            wf_service.trg_validate(uid, 'procurement.order', pro, 'button_check', cr)
        return picking_id

    def check_reject(self, cr, uid, ids):
        res = {
           'approver_id':uid
        }
        self.write(cr, uid, ids, res)
        return True

    def check_approval(self, cr, uid, ids, context=None):
        res = {
           'approver_id':uid
        }
        self.write(cr, uid, ids, res)
        return True

    def action_receive_products(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display internal move of given indent ids.
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time'
        picking_id = self.browse(cr, uid, ids[0], context=context).picking_id.id
        res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'view_picking_form')
        result = {
            'name': _('Receive Product'),
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
indent_indent()

class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    def _get_indent(self, cr, uid, ids, name, args, context=None):
        result = {}
        indent_obj = self.pool.get('indent.indent')
        for order in self.browse(cr, uid, ids, context=context):
            indent_id = False
            if order.origin:
                indent_ids = indent_obj.search(cr, uid, [('name', '=', order.origin)], context=context)
                indent_id = indent_ids and indent_ids[0] or False
            result[order.id] = indent_id
        return result

    _columns = {
        'indent_id': fields.function(_get_indent, relation='indent.indent', type="many2one", string='Indent', store=True),
        'indentor_id': fields.related('indent_id', 'indentor_id', type='many2one', relation='res.users', string='Indentor', store=True, readonly=True),
        'indent_date': fields.related('indent_id', 'indent_date', type='datetime', relation='indent.indent', string='Indent Date', store=True, readonly=True),
    }
purchase_order()

class indent_product_lines(osv.Model):
    _name = 'indent.product.lines'
    _description = 'Indent Product Lines'

    def _amount_subtotal(self, cr, uid, ids, name, args, context=None):
        result = {}
        for line in self.browse(cr, uid, ids, context=context):
            result[line.id] = (line.product_uom_qty * line.price_unit)
        return result

    _columns = {
        'indent_id': fields.many2one('indent.indent', 'Indent', required=True, ondelete='cascade'),
        'name': fields.text('Description', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'original_product_id': fields.many2one('product.product', 'Original Product'),
        'type': fields.selection([('make_to_stock', 'Stock'), ('make_to_order', 'Purchase')], 'Procure', required=True,
         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
        'product_uom_qty': fields.float('Quantity Required', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'price_unit': fields.float('Price', required=True, digits_compute= dp.get_precision('Product Price'), help="Price computed based on the last purchase order approved."),
        'price_subtotal': fields.function(_amount_subtotal, string='Subtotal', digits_compute= dp.get_precision('Account'), store=True),
        'qty_available': fields.float('In Stock'),
        'virtual_available': fields.float('Forecasted Qty'),
        'delay': fields.float('Lead Time', required=True),
        'name': fields.text('Purpose', required=True),
        'specification': fields.text('Specification'),
    }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'type': 'make_to_order',
        'delay': 0.0,
    }

    def onchange_product_id(self, cr, uid, ids, product_id=False, product_uom_qty=0.0, product_uom=False, price_unit=0.0, qty_available=0.0, virtual_available=0.0, name='', analytic_account_id=False, indent_type=False, context=None):
        result = {}
        product_obj = self.pool.get('product.product')
        if not product_id:
            return {'value': {'product_uom_qty': 1.0, 'product_uom': False, 'price_unit': 0.0, 'qty_available': 0.0, 'virtual_available': 0.0, 'name': '', 'delay': 0.0}}

        product = product_obj.browse(cr, uid, product_id, context=context)
        if indent_type and indent_type == 'existing' and product.type != 'service':
            raise osv.except_osv(_("Warning !"), _("You must select a service type product."))
        
        if not product.seller_ids:
            raise osv.except_osv(_("Warning !"), _("You must define at least one supplier for this product."))
        
        if product.qty_available and product.virtual_available > 0:
            result['type'] = 'make_to_stock'
        
        result['name'] = product_obj.name_get(cr, uid, [product.id])[0][1]
        result['product_uom'] = product.uom_id.id
        result['price_unit'] = product.standard_price
        result['qty_available'] = product.qty_available
        result['virtual_available'] = product.virtual_available
        result['delay'] = product.seller_ids[0].delay
        result['specification'] = product.description_purchase
        return {'value': result}
    
indent_product_lines()

class stock_picking(osv.Model):
    _inherit = 'stock.picking'
 
    def action_confirm(self, cr, uid, ids, context=None):
        #Implement method that will check further verification for authority
        return super(stock_picking, self).action_confirm(cr, uid, ids, context=context)
 
    def check_approval(self, cr, uid, ids):
        #Implement method that will check further verification for authority
        return True
     
stock_picking()