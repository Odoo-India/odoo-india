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
from datetime import timedelta

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
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
        'employee_id': fields.many2one('res.users', 'Employee'),
        'manager_id': fields.related('department_id', 'manager_id', readonly=True, type='many2one', relation='res.users', string='Department Manager', store=True, states={'draft': [('readonly', False)]}),
        'department_id': fields.many2one('stock.location', 'Department', required=True, readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}, domain=[('can_request','=', True)]),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', ondelete="cascade",readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
        'requirement': fields.selection([('ordinary', 'Ordinary'), ('urgent', 'Urgent')], 'Requirement', readonly=True, required=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
        'type': fields.selection([('new', 'Store'), ('existing', 'Repairing')], 'Type', required=True, track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]}),
        'product_lines': fields.one2many('indent.product.lines', 'indent_id', 'Products', readonly=True, states={'draft': [('readonly', False)], 'waiting_approval': [('readonly', False)]}),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'description': fields.text('Item Description', readonly=True, states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one('res.company', 'Company', readonly=True, states={'draft': [('readonly', False)]}),
        'indent_authority_ids': fields.one2many('document.authority.instance', 'indent_id', 'Authority', readonly=True, states={'draft': [('readonly', False)]}),
        'active': fields.boolean('Active'),
        'item_for': fields.selection([('store', 'Store'), ('capital', 'Capital')], 'Item For', readonly=True, states={'draft': [('readonly', False)]}),
        'amount_total': fields.function(_total_amount, type="float", string='Total',
            store={
                'indent.indent': (lambda self, cr, uid, ids, c={}: ids, ['product_lines'], 20),
                'indent.product.lines': (_get_product_line, ['price_subtotal', 'product_uom_qty', 'indent_id'], 20),
            },
            ),
        'maize': fields.char('Maize', size=256, readonly=True),
        'fiscalyear': fields.char('Year', readonly=True),
        'state':fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('waiting_approval', 'Waiting For Approval'), ('inprogress', 'Inprogress'), ('received', 'Received'), ('reject', 'Rejected')], 'State', readonly=True, track_visibility='onchange'),
    }
    
    def _default_employee_id(self, cr, uid, context=None):
        return uid

    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    def _get_required_date(self, cr, uid, context=None):
        return datetime.datetime.strftime(datetime.datetime.today() + timedelta(days=7), DEFAULT_SERVER_DATETIME_FORMAT)

    _defaults = {
        'state': 'draft',
        'indent_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'required_date': _get_required_date,
        'indentor_id': lambda self, cr, uid, context: uid,
        'employee_id': _default_employee_id,
        'requirement': 'ordinary',
        'type': 'new',
        'item_for':'store',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'indent.indent', context=c),
        'active': True,
        'fiscalyear': str(time.strptime(time.strftime('%Y', time.localtime()),'%Y').tm_year)+str(time.strptime(time.strftime('%Y', time.localtime()),'%Y').tm_year+1)
    }
    
    def _needaction_domain_get(self, cr, uid, context=None):
        return [('state', '=', 'waiting_approval')]

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'indent.indent'),
            'indent_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'required_date': self._get_required_date(cr, uid, context=context),
            'picking_id': False,
            'indent_authority_ids': [],
            'state': 'draft',
        })
        return super(indent_indent, self).copy(cr, uid, id, default, context=context)

    def onchange_item(self, cr, uid, ids, item_for=False, context=None):
        result = {}
        if not item_for or item_for == 'store':
            result['analytic_account_id'] = False
        return {'value': result}

indent_indent()

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
        'type': fields.selection([('make_to_stock', 'Assign from stock'), ('make_to_order', 'Purchase order')], 'Procure by', required=True,
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
        if analytic_account_id:
            prod_ids = product_obj.search(cr, uid, [('default_code', '=like', '%s%%' % '0152')], context=context)
            if product_id not in prod_ids:
                raise osv.except_osv(_("Warning !"), _("You must select a product whose code start with '0152'."))
        product = product_obj.browse(cr, uid, product_id, context=context)
        if indent_type and indent_type == 'existing' and product.type != 'service':
            raise osv.except_osv(_("Warning !"), _("You must select a service type product."))
        if not product.seller_ids:
            raise osv.except_osv(_("Warning !"), _("You must define at least one supplier for this product."))
        result['name'] = product_obj.name_get(cr, uid, [product.id])[0][1]
        result['product_uom'] = product.uom_id.id
        result['price_unit'] = product.standard_price
        result['qty_available'] = product.qty_available
        result['virtual_available'] = product.virtual_available
        result['delay'] = product.seller_ids[0].delay
        return {'value': result}

indent_product_lines()

class document_authority(osv.Model):
    _name = 'document.authority'
    _description = 'Document Authority'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res

        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(record.id, record.name.name) for record in self.browse(cr, uid , ids, context=context)]

    _columns = {
        'name': fields.many2one('res.users', 'Authority', required=True),
        'document': fields.selection([('indent','Indent'), ('order','Purchase Order'), ('picking','Picking')], 'Document', required=True),
        'priority': fields.integer('Priority'),
        'active': fields.boolean('Active', help="If the active field is set to False, it will allow you to hide the document authority without removing it."),
        'description': fields.text('Description'),
    }

    _defaults = {
        'active': True,
    }

document_authority()

class document_authority_instance(osv.Model):
    _name = 'document.authority.instance'
    _description = 'Document Authority Instance'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        # name_get may receive int id instead of an id list
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(record.id, record.name.name) for record in self.browse(cr, uid , ids, context=context)]

    _columns = {
        'indent_id': fields.many2one('indent.indent', 'Indent', required=True, ondelete='cascade'),
        'name': fields.many2one('res.users', 'Authority', required=True),
        'document': fields.selection([('indent','Indent'), ('order','Purchase Order'), ('picking','Picking')], 'Document', required=True),
        'priority': fields.integer('Priority'),
        'description': fields.text('Description'),
        'date': fields.datetime('Date'),
        'state':fields.selection([('pending','Pending'), ('approve','Approved'), ('reject','Rejected')], 'State', required=True)
    }
    _defaults = {
        'state': 'pending',
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

document_authority_instance()

