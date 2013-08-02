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
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import amount_to_text_en as text
from openerp import tools
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

SERIES = [
    ('repair', 'Repair'),
    ('purchase', 'Purchase'),
    ('store', 'Store')
]

class ir_attachment(osv.Model):
    _inherit = 'ir.attachment'

    def create(self, cr, uid, values, context=None):
        res_id = super(ir_attachment, self).create(cr, uid, values, context)
        if values.get('res_model') == 'indent.indent' and values.get('res_id'):
            self.pool.get('indent.indent').write(cr, uid, values['res_id'], {'attachment_id': res_id},context)
        return res_id

ir_attachment()

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
        'indent_date': fields.datetime('Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'required_date': fields.datetime('Required Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'attachment_id': fields.many2one('ir.attachment', 'Attachment'),
        'print_report': fields.related('attachment_id', 'datas', type='binary', string='Indent Report'),
        'indentor_id': fields.many2one('res.users', 'Indentor', required=True, readonly=True, track_visibility='always', states={'draft': [('readonly', False)]}),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'employee_department_id': fields.related('employee_id', 'department_id',readonly=True, type='many2one', relation='hr.department', string='Employee Department', store=True, states={'draft': [('readonly', False)]}),
        'department_id': fields.many2one('stock.location', 'Department', required=True, readonly=True, track_visibility='onchange', states={'draft': [('readonly', False)]}),
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
        employees = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if not employees:
            raise osv.except_osv(_("Warning !"),_('You must define an employee and assign the related user to that employee.'))
        return employees and employees[0] or False

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
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'indent.indent', context=c),
        'active': True,
        'fiscalyear': str(time.strptime(time.strftime('%Y', time.localtime()),'%Y').tm_year)+str(time.strptime(time.strftime('%Y', time.localtime()),'%Y').tm_year+1)
    }

    def create(self, cr, uid, vals, context=None):
        if vals.get('department_id'):
            location = self.pool.get('stock.location').browse(cr, uid, vals.get('department_id'), context=context).location_id
            if location and location.seq_id and not vals.get('maize') and not vals.get('contract'):
                seq = location.seq_id.code
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, seq)
            elif vals.get('contract'):
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'contract.maize')
        return super(indent_indent, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        con = self.browse(cr,uid,ids)[0].contract
        if vals.get('department_id') and not con:
            location = self.pool.get('stock.location').browse(cr, uid, vals.get('department_id'), context=context).location_id
            if location and location.seq_id:
                seq = location.seq_id.code
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, seq)
        return super(indent_indent, self).write(cr, uid, ids, vals, context=context)

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

    def indent_confirm(self, cr, uid, ids, context=None):
        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = employee_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_manager_list
        obj_hr = self.pool.get('hr.employee')
        document_authority_obj = self.pool.get('document.authority')
        document_authority_instance_obj = self.pool.get('document.authority.instance')
        document_authority_ids = document_authority_obj.search(cr, uid, [('document', '=', 'indent')], context=context)
        for indent in self.browse(cr, uid, ids, context=context): 
            if not indent.product_lines:
                raise osv.except_osv(_('Warning!'),_('You cannot confirm an indent which has no line.'))

            authorities = []
            for authority in document_authority_obj.browse(cr, uid, document_authority_ids, context=context):
                if authority.name.id not in authorities:
                    document_authority_instance_obj.create(cr, uid, {'name': authority.name.id, 'document': 'indent', 'indent_id': indent.id, 'priority': authority.priority}, context=context)
                    authorities.append(authority.name.id)

            employee_parent_ids = obj_hr.search(cr, uid, [])
            employee_parents = obj_hr.read(cr, uid, employee_parent_ids, ['coach_id'])
            employee_tree = dict([(item['id'], item['coach_id'][0]) for item in employee_parents if item['coach_id']])
            if not indent.employee_id.id:
                raise osv.except_osv(_('Configuration Error!'), _('Create related employee for %s' % indent.indentor_id.name))
            parent_employee_ids = _create_parent_category_list(indent.employee_id.id, [indent.employee_id.id])
            new_parent_employee_id = list(reversed(parent_employee_ids))
            priority=11
            for auth in new_parent_employee_id:
                emp = obj_hr.browse(cr,uid,auth,context=context)
                if emp.user_id and not emp.absent:
                    if emp.user_id.id not in authorities:
                        document_authority_instance_obj.create(cr, uid, {'name': emp.user_id.id, 'document': 'indent', 'indent_id': indent.id, 'priority': priority}, context=context)
                        priority=priority+1
                        authorities.append(emp.user_id.id)

            # Add all authorities of the indent as followers
            for authority in indent.indent_authority_ids:
                if authority.name and authority.name.partner_id and authority.name.partner_id.id not in indent.message_follower_ids:
                    self.write(cr, uid, [indent.id], {'message_follower_ids': [(4, authority.name.partner_id.id)]}, context=context)

        self.write(cr, uid, ids, {'state': 'waiting_approval'}, context=context)
        return True

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
        if indent.contract or indent.type == 'existing':
            pro_ids  = proc_obj.search(cr,uid,[('origin','=',indent.name)])
        for pro in pro_ids:
            wf_service.trg_validate(uid, 'procurement.order', pro, 'button_check', cr)
        return picking_id

    def check_approval(self, cr, uid, ids):
        document_authority_instance_obj = self.pool.get('document.authority.instance')
        for indent in self.browse(cr, uid, ids):
            authorities = [(authority.id, authority.name.id, authority.priority, authority.state, authority.name.name) for authority in indent.indent_authority_ids]
            sort_authorities = sorted(authorities, key=lambda element: (element[2]))
            count = 0
            count_auth = 0
            for authority in sort_authorities:
                count += 1
                if authority[1] == uid:
                    count_auth += 1
                    if authority[3] == 'approve':
                        raise osv.except_osv(_("Warning !"),_('You have already approved an indent.'))
                    write_ids = [(auth[0], auth[3]) for auth in sort_authorities][count:]
                    document_authority_instance_obj.write(cr, uid, [authority[0]], {'state': 'approve'})
                    msg = 'Indent is approved by <b>%s</b>.' % (authority[4])
                    self.message_post(cr, uid, [indent.id], body=msg)
                    if count_auth == 1:
                        for write_id in write_ids:
                            desc = document_authority_instance_obj.browse(cr, uid, write_id[0]).description
                            description = 'Approved by higher authority - %s' %(authority[4],)
                            if desc:
                                description = 'Approved by higher authority - %s' %(authority[4],) + '\n' + desc
                            document_authority_instance_obj.write(cr, uid, [write_id[0]], {'description': description})

        for indent in self.browse(cr, uid, ids):
            authorities = [(authority.id, authority.priority, authority.state) for authority in indent.indent_authority_ids]
            sort_authorities = sorted(authorities, key=lambda element: (element[1]))
            for authority in sort_authorities:
                if authority[2] == 'approve':
                    return True
                elif authority[2] == 'pending' or authority[2] == 'reject':
                    return False
        return True

    def check_reject(self, cr, uid, ids):
        document_authority_instance_obj = self.pool.get('document.authority.instance')
        for indent in self.browse(cr, uid, ids):
            authorities = [(authority.id, authority.name.id, authority.priority, authority.state, authority.name.name) for authority in indent.indent_authority_ids]
            sort_authorities = sorted(authorities, key=lambda element: (element[2]))
            count = 0
            count_auth = 0
            for authority in sort_authorities:
                count += 1
                if authority[1] == uid:
                    count_auth += 1
                    if authority[3] == 'reject':
                        raise osv.except_osv(_("Warning !"),_('You have already rejected an indent.'))
                    write_ids = [(auth[0], auth[3]) for auth in sort_authorities][count:]
                    document_authority_instance_obj.write(cr, uid, [authority[0]], {'state': 'reject'})
                    msg = 'Indent is rejected by <b>%s</b>.' % (authority[4])
                    self.message_post(cr, uid, [indent.id], body=msg)
                    if count_auth == 1:
                        for write_id in write_ids:
                            desc = document_authority_instance_obj.browse(cr, uid, write_id[0]).description
                            description = 'Rejected by higher authority - %s' %(authority[4],)
                            if desc:
                                description = 'Rejected by higher authority - %s' %(authority[4],) + '\n' + desc
                            document_authority_instance_obj.write(cr, uid, [write_id[0]], {'description': description})

        for indent in self.browse(cr, uid, ids):
            authorities = [(authority.id, authority.priority, authority.state) for authority in indent.indent_authority_ids]
            sort_authorities = sorted(authorities, key=lambda element: (element[1]))
            for authority in sort_authorities:
                if authority[2] == 'approve' or authority[2] == 'pending':
                    return False
                elif authority[2] == 'reject':
                    return True
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

    def _prepare_indent_line_procurement(self, cr, uid, indent, line, move_id, date_planned, context=None):
        warehouse_obj = self.pool.get('stock.warehouse')
        company_ids = self.pool.get('res.company').search(cr, uid, [('name', '=', 'MAIZE PRODUCTS')], context=context)
        company_id = company_ids and company_ids[0] or False
        warehouse_ids = warehouse_obj.search(cr, uid, [('company_id', '=', company_id)], context=context)
        warehouse_id = warehouse_ids and warehouse_ids[0] or False
        location_id = warehouse_obj.browse(cr, uid, warehouse_id, context=context).lot_input_id.id
        res = {
            'name': line.name,
            'origin': indent.name,
            'indent_id': indent.id,
            'indentor_id': indent.indentor_id.id,
            'department_id': indent.department_id.id,
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

    def _get_date_planned(self, cr, uid, indent, line, start_date, context=None):
        date_planned = datetime.datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT) + relativedelta(days=line.delay or 0.0)
        return date_planned

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

    def create_series_sequence(self, cr, uid, vals, context=None):
        series_obj = self.pool.get('product.order.series')
        type_name= series_obj.browse(cr,uid,vals['po_series_id']).code
        type = self.pool.get('ir.sequence.type').create(cr,uid,{'name':'maize'+type_name,'code':type_name})
        code = self.pool.get('ir.sequence.type').browse(cr,uid,type).code
        seq = {
            'name': series_obj.browse(cr,uid,vals['po_series_id']).code,
            'implementation':'standard',
            'prefix': series_obj.browse(cr,uid,vals['po_series_id']).code+"/",
            'padding': 4,
            'number_increment': 1,
            'code':code
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        return self.pool.get('ir.sequence').create(cr, uid, seq)

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
        'type': fields.selection([('make_to_stock', 'Assign from stock'), ('make_to_order', 'Make new purchase order')], 'Procurement Method', required=True,
         help="From stock: When needed, the product is taken from the stock or we wait for replenishment.\nOn order: When needed, the product is purchased or produced."),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product UoS'), required=True),
        'product_uom': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_subtotal': fields.function(_amount_subtotal, string='Subtotal', digits_compute= dp.get_precision('Account'), store=True),
        'qty_available': fields.float('Stock'),
        'virtual_available': fields.float('Forecasted Qty'),
        'delay': fields.float('Lead Time', required=True),
        'name': fields.text('Purpose', required=True),
        'specification': fields.text('Item Specification'),
    }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
#        'product_uom' : _get_uom_id,
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
        # name_get may receive int id instead of an id list
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

class stock_picking(osv.Model):
    _inherit = 'stock.picking'

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
        'picking_authority_ids': fields.one2many('picking.authority', 'picking_id', 'Authority'),
        'maize': fields.char('Maize', size=256, readonly=True),
        'maize_in': fields.char('Maize', size=256, readonly=True),
        'maize_out': fields.char('Maize', size=256, readonly=True),
        'maize_receipt': fields.char('Maize', size=256, readonly=True),
        'lr_no': fields.char("LR No",size=64),
        'lr_date': fields.date("LR Date"),
        'transporter':fields.char("Transporter",size=256),
        'hpressure':fields.integer("HPressure"),
        'dest_from': fields.char("Destination From",size=64),
        'dest_to': fields.char("Destination To",size=64),
        'lab_no':fields.integer("Lab No"),
        'gp_no': fields.integer("Gate Pass No"),
        'gp_year': fields.char("GP Year",size=64),
        'remark1': fields.char("Remark1",size=256),
        'remark2': fields.char("remark2",size=256),
        'case_code': fields.boolean("Cash Code"),
        'challan_no': fields.char("Challan Number",size=256),
        'despatch_mode': fields.selection([('person','By Person'),
                                           ('scooter','By Scooter'),
                                           ('tanker','By Tanker'),
                                           ('truck','By Truck'),
                                           ('auto_rickshaw','By Auto Rickshaw'),
                                           ('loading_rickshaw','By Loading Rickshaw'),
                                           ('tempo','By Tempo'),
                                           ('metador','By Metador'),
                                           ('rickshaw_tempo','By Rickshaw Tempo'),
                                           ('cart','By Cart'),
                                           ('cycle','By Cycle'),
                                           ('pedal_rickshaw','By Pedal Rickshaw'),
                                           ('car','By Car'),
                                           ('post_parcel','By Post Parcel'),
                                           ('courier','By Courier'),
                                           ('tractor','By Tractor'),
                                           ('hand_cart','By Hand Cart'),
                                           ('camel_cart','By Camel Cart'),
                                           ('others','Others'),],"Despatch Mode"),
        'other_dispatch': fields.char("Other Dispatch",size=256),
        'series_id':fields.selection(SERIES, 'Series'),
    }

    def action_confirm(self, cr, uid, ids, context=None):
        picking_authority_obj = self.pool.get('picking.authority')
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.type == 'internal':
                if picking.indent_id and picking.indent_id.employee_id and picking.indent_id.employee_id.coach_id and picking.indent_id.employee_id.coach_id.user_id and picking.indent_id.employee_id.coach_id.user_id.id:
                    picking_authority_obj.create(cr, uid, {'name': picking.indent_id.employee_id.coach_id.user_id.id, 'document': 'picking', 'picking_id': picking.id, 'priority': 1}, context=context)
                if picking.indent_id and picking.indent_id.employee_id and picking.indent_id.employee_id.user_id and picking.indent_id.employee_id.user_id.id:
                    picking_authority_obj.create(cr, uid, {'name': picking.indent_id.employee_id.user_id.id, 'document': 'picking', 'picking_id': picking.id, 'priority': 2}, context=context)
        return super(stock_picking, self).action_confirm(cr, uid, ids, context=context)

    def check_approval(self, cr, uid, ids):
        picking_authority_obj = self.pool.get('picking.authority')
        for picking in self.browse(cr, uid, ids):
            if picking.type == 'internal':
                authorities = [(authority.id, authority.name.id, authority.priority, authority.state, authority.name.name) for authority in picking.picking_authority_ids]
                sort_authorities = sorted(authorities, key=lambda element: (element[2]))
                count = 0
                for authority in sort_authorities:
                    count += 1
                    if authority[1] == uid:
                        write_ids = [(auth[0], auth[3]) for auth in sort_authorities][count:]
                        picking_authority_obj.write(cr, uid, [authority[0]], {'state': 'approve'})
                        for write_id in write_ids:
                            desc = picking_authority_obj.browse(cr, uid, write_id[0]).description
                            description = 'Approved by higher authority - %s' %(authority[4],)
                            if desc:
                                description = 'Approved by higher authority - %s' %(authority[4],) + '\n' + desc
                            picking_authority_obj.write(cr, uid, [write_id[0]], {'description': description})
                        break

        for picking in self.browse(cr, uid, ids):
            if picking.type == 'internal':
                authorities = [(authority.id, authority.priority, authority.state) for authority in picking.picking_authority_ids]
                sort_authorities = sorted(authorities, key=lambda element: (element[1]))
                for authority in sort_authorities:
                    if authority[2] == 'approve':
                        return True
                    elif authority[2] == 'pending' or authority[2] == 'reject':
                        return False
        return True

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        """ Makes partial picking and moves done.
        @param partial_datas : Dictionary containing details of partial picking
              like partner_id, partner_id, delivery_date,
              delivery moves with product_id, product_qty, uom
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        else:
            context = dict(context)
        res = {}
        move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        currency_obj = self.pool.get('res.currency')
        uom_obj = self.pool.get('product.uom')
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids, context=context):
            new_picking = None
            complete, too_many, too_few = [], [], []
            move_product_qty, prodlot_ids, product_avail, partial_qty, product_uoms = {}, {}, {}, {}, {}
            for move in pick.move_lines:
                if move.state in ('done', 'cancel'):
                    continue
                partial_data = partial_datas.get('move%s'%(move.id), {})
                product_qty = partial_data.get('product_qty',0.0)
                move_product_qty[move.id] = product_qty
                product_uom = partial_data.get('product_uom',False)
                product_price = partial_data.get('product_price',0.0)
                product_currency = partial_data.get('product_currency',False)
                prodlot_id = partial_data.get('prodlot_id')
                prodlot_ids[move.id] = prodlot_id
                product_uoms[move.id] = product_uom
                partial_qty[move.id] = uom_obj._compute_qty(cr, uid, product_uoms[move.id], product_qty, move.product_uom.id)
                if move.product_qty == partial_qty[move.id]:
                    complete.append(move)
                elif move.product_qty > partial_qty[move.id]:
                    too_few.append(move)
                else:
                    too_many.append(move)

                # Average price computation
                if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
                    product = product_obj.browse(cr, uid, move.product_id.id)
                    move_currency_id = move.company_id.currency_id.id
                    context['currency_id'] = move_currency_id
                    qty = uom_obj._compute_qty(cr, uid, product_uom, product_qty, product.uom_id.id)

                    if product.id in product_avail:
                        product_avail[product.id] += qty
                    else:
                        product_avail[product.id] = product.qty_available

                    if qty > 0:
                        new_price = currency_obj.compute(cr, uid, product_currency,
                                move_currency_id, product_price)
                        new_price = uom_obj._compute_price(cr, uid, product_uom, new_price,
                                product.uom_id.id)
                        if product.qty_available <= 0:
                            new_std_price = new_price
                        else:
                            # Get the standard price
                            amount_unit = product.price_get('standard_price', context=context)[product.id]
                            new_std_price = ((amount_unit * product_avail[product.id])\
                                + (new_price * qty))/(product_avail[product.id] + qty)
                        # Write the field according to price type field
                        product_obj.write(cr, uid, [product.id], {'standard_price': new_std_price})

                        # Record the values that were chosen in the wizard, so they can be
                        # used for inventory valuation if real-time valuation is enabled.
                        move_obj.write(cr, uid, [move.id],
                                {'price_unit': product_price,
                                 'price_currency_id': product_currency})

            for move in too_few:
                product_qty = move_product_qty[move.id]
                if not new_picking:
                    new_picking_name = pick.name
                    new_picking = self.copy(cr, uid, pick.id,
                        {
                            'name': new_picking_name,
                            'move_lines' : [],
                            'state':'draft',
                        })
                if product_qty != 0:
                    defaults = {
                            'product_qty' : product_qty,
                            'product_uos_qty': product_qty, #TODO: put correct uos_qty
                            'picking_id' : new_picking,
                            'state': 'assigned',
                            'move_dest_id': False,
                            'price_unit': move.price_unit,
                            'product_uom': product_uoms[move.id]
                    }
                    prodlot_id = prodlot_ids[move.id]
                    if prodlot_id:
                        defaults.update(prodlot_id=prodlot_id)
                    move_obj.copy(cr, uid, move.id, defaults)
                move_obj.write(cr, uid, [move.id],
                    {
                        'product_qty': move.product_qty - partial_qty[move.id],
                        'product_uos_qty': move.product_qty - partial_qty[move.id], #TODO: put correct uos_qty
                        'prodlot_id': False,
                        'tracking_id': False,
                    })

            if new_picking:
                move_obj.write(cr, uid, [c.id for c in complete], {'picking_id': new_picking})
            for move in complete:
                defaults = {'product_uom': product_uoms[move.id], 'product_qty': move_product_qty[move.id]}
                if prodlot_ids.get(move.id):
                    defaults.update({'prodlot_id': prodlot_ids[move.id]})
                move_obj.write(cr, uid, [move.id], defaults)
            for move in too_many:
                product_qty = move_product_qty[move.id]
                defaults = {
                    'product_qty' : product_qty,
                    'product_uos_qty': product_qty, #TODO: put correct uos_qty
                    'product_uom': product_uoms[move.id]
                }
                prodlot_id = prodlot_ids.get(move.id)
                if prodlot_ids.get(move.id):
                    defaults.update(prodlot_id=prodlot_id)
                if new_picking:
                    defaults.update(picking_id=new_picking)
                move_obj.write(cr, uid, [move.id], defaults)

            # At first we confirm the new picking (if necessary)
            if new_picking:
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_confirm', cr)
                # Then we finish the good picking
                self.write(cr, uid, [pick.id], {'backorder_id': new_picking})
                self.action_move(cr, uid, [new_picking], context=context)
                wf_service.trg_validate(uid, 'stock.picking', new_picking, 'button_done', cr)
                wf_service.trg_write(uid, 'stock.picking', pick.id, cr)
                delivered_pack_id = new_picking
                back_order_name = self.browse(cr, uid, delivered_pack_id, context=context).name
                self.message_post(cr, uid, ids, body=_("Back order <em>%s</em> has been <b>created</b>.") % (back_order_name), context=context)
            else:
                self.action_move(cr, uid, [pick.id], context=context)
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
                delivered_pack_id = pick.id

            delivered_pack = self.browse(cr, uid, delivered_pack_id, context=context)
            res[pick.id] = {'delivered_picking': delivered_pack.id or False}

        return res

stock_picking()

class picking_authority(osv.Model):
    _name = 'picking.authority'
    _description = 'Picking Authority'

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return res
        # name_get may receive int id instead of an id list
        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(record.id, record.name.name) for record in self.browse(cr, uid , ids, context=context)]

    _columns = {
        'picking_id': fields.many2one('stock.picking', 'Picking', required=True, ondelete='cascade'),
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

picking_authority()

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
        'maize': fields.char('Maize PO Number', size=256, readonly=True),
        'contract_name': fields.char('Contract Name', size=256, readonly=True),
        'voucher_id': fields.many2one('account.voucher', 'Payment'),
    }

    def _prepare_order_picking(self, cr, uid, order, context=None):
        return {
            'name': False,
            'origin': order.name + ((order.origin and (':' + order.origin)) or ''),
            'date': self.date_to_datetime(cr, uid, order.date_order, context),
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'invoice_state': '2binvoiced' if order.invoice_method == 'picking' else 'none',
            'type': 'in',
            'partner_id': order.dest_address_id.id or order.partner_id.id,
            'purchase_id': order.id,
            'company_id': order.company_id.id,
            'move_lines' : [],
            'voucher_id': order.voucher_id.id,
        }

purchase_order()

class purchase_order_line(osv.Model):
    _inherit = 'purchase.order.line'

    _columns = {
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'indentor_id': fields.many2one('res.users', 'Indentor'),
        'department_id': fields.many2one('stock.location', 'Department'),
    }

purchase_order_line()

class purchase_requisition(osv.Model):
    _inherit = 'purchase.requisition'

    def _get_indent(self, cr, uid, ids, name, args, context=None):
        result = {}
        indent_obj = self.pool.get('indent.indent')
        for requisition in self.browse(cr, uid, ids, context=context):
            indent_id = False
            if requisition.origin:
                indent_ids = indent_obj.search(cr, uid, [('name', '=', requisition.origin)], context=context)
                indent_id = indent_ids and indent_ids[0] or False
            result[requisition.id] = indent_id
        return result

    _columns = {
        'indent_id': fields.function(_get_indent, relation='indent.indent', type="many2one", string='Indent', store=True),
        'indentor_id': fields.related('indent_id', 'indentor_id', type='many2one', relation='res.users', string='Indentor', store=True, readonly=True),
        'indent_date': fields.related('indent_id', 'indent_date', type='datetime', relation='indent.indent', string='Indent Date', store=True, readonly=True),
        'maize': fields.char('Maize', size=256, readonly=True),
    }

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        """
        Create New RFQ for Supplier
        """
        if context is None:
            context = {}
        assert partner_id, 'Supplier should be specified'
        purchase_order = self.pool.get('purchase.order')
        purchase_order_line = self.pool.get('purchase.order.line')
        res_partner = self.pool.get('res.partner')
        fiscal_position = self.pool.get('account.fiscal.position')
        supplier = res_partner.browse(cr, uid, partner_id, context=context)
        supplier_pricelist = supplier.property_product_pricelist_purchase or False
        res = {}
        for requisition in self.browse(cr, uid, ids, context=context):
            if supplier.id in filter(lambda x: x, [rfq.state <> 'cancel' and rfq.partner_id.id or None for rfq in requisition.purchase_ids]):
                raise osv.except_osv(_('Warning!'), _('You have already one %s purchase order for this partner, you must cancel this purchase order to create a new quotation.') % rfq.state)
            location_id = requisition.warehouse_id.lot_input_id.id
            purchase_id = purchase_order.create(cr, uid, {
                        'origin': requisition.origin,
                        'partner_id': supplier.id,
                        'pricelist_id': supplier_pricelist.id,
                        'location_id': location_id,
                        'company_id': requisition.company_id.id,
                        'fiscal_position': supplier.property_account_position and supplier.property_account_position.id or False,
                        'requisition_id':requisition.id,
                        'notes':requisition.description,
                        'warehouse_id':requisition.warehouse_id.id,
            }, context=context)
            res[requisition.id] = purchase_id
            for line in requisition.line_ids:
                product = line.product_id
                seller_price, qty, default_uom_po_id, date_planned = self._seller_details(cr, uid, line, supplier, context=context)
                taxes_ids = product.supplier_taxes_id
                taxes = fiscal_position.map_tax(cr, uid, supplier.property_account_position, taxes_ids)
                purchase_order_line.create(cr, uid, {
                    'order_id': purchase_id,
                    'name': product.partner_ref,
                    'product_qty': qty,
                    'product_id': product.id,
                    'product_uom': default_uom_po_id,
                    'price_unit': seller_price,
                    'date_planned': date_planned,
                    'taxes_id': [(6, 0, taxes)],
                }, context=context)
            self.pool.get('purchase.requisition').write(cr,uid,requisition.id,{'purchase_ids':[(4,purchase_id)]})
        return res

purchase_requisition()

class procurement_order(osv.osv):
    _inherit = 'procurement.order'

    _columns = {
        'indent_id': fields.many2one('indent.indent', 'Indent'),
        'indentor_id': fields.many2one('res.users', 'Indentor'),
        'department_id': fields.many2one('stock.location', 'Department'),
    }

    def make_po(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        @return: New created Purchase Orders procurement wise
        """
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        seq_obj = self.pool.get('ir.sequence')
        warehouse_obj = self.pool.get('stock.warehouse')
        requisition_obj = self.pool.get('purchase.requisition')
        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            partner_id = partner.id
            pricelist_id = partner.property_product_pricelist_purchase.id
            warehouse_id = warehouse_obj.search(cr, uid, [('company_id', '=', procurement.company_id.id or company.id)], context=context)
            uom_id = procurement.product_id.uom_po_id.id

            qty = uom_obj._compute_qty(cr, uid, procurement.product_uom.id, procurement.product_qty, uom_id)
            if seller_qty:
                qty = max(qty,seller_qty)

            price = pricelist_obj.price_get(cr, uid, [pricelist_id], procurement.product_id.id, qty, partner_id, {'uom': uom_id})[pricelist_id]

            schedule_date = self._get_purchase_schedule_date(cr, uid, procurement, company, context=context)
            purchase_date = self._get_purchase_order_date(cr, uid, procurement, company, schedule_date, context=context)

            #Passing partner_id to context for purchase order line integrity of Line name
            new_context = context.copy()
            new_context.update({'lang': partner.lang, 'partner_id': partner_id})

            product = prod_obj.browse(cr, uid, procurement.product_id.id, context=new_context)
            taxes_ids = procurement.product_id.supplier_taxes_id
            taxes = acc_pos_obj.map_tax(cr, uid, partner.property_account_position, taxes_ids)

            name = ''
            if product.description_purchase:
                name = product.description_purchase
            line_vals = {
                'name': name,
                'indent_id': procurement.indent_id and procurement.indent_id.id or False,
                'indentor_id': procurement.indentor_id and procurement.indentor_id.id or False,
                'department_id': procurement.department_id and procurement.department_id.id or False,
                'product_qty': qty,
                'product_id': procurement.product_id.id,
                'product_uom': uom_id,
                'price_unit': price or 0.0,
                'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'move_dest_id': False,
                'taxes_id': [(6,0,taxes)],
            }
            name = seq_obj.get(cr, uid, 'purchase.order') or _('PO: %s') % procurement.name
            po_vals = {
                'name': name,
                'origin': procurement.origin,
                'partner_id': partner_id,
                'location_id': procurement.location_id.id,
                'warehouse_id': warehouse_id and warehouse_id[0] or False,
                'pricelist_id': pricelist_id,
                'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': procurement.company_id.id,
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                'payment_term_id': partner.property_supplier_payment_term.id or False,
            }
            res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=new_context)
            requisition_id = False
            if procurement.product_id.purchase_requisition:
                requisition_id = requisition_obj.create(cr, uid, 
                    {
                        'origin': procurement.origin,
                        'date_end': procurement.date_planned,
                        'warehouse_id':warehouse_id and warehouse_id[0] or False,
                        'company_id':procurement.company_id.id,
                        'line_ids': [(0,0,{
                            'product_id': procurement.product_id.id,
                            'product_uom_id': procurement.product_uom.id,
                            'product_qty': procurement.product_qty
                        })],
                    })
                requisition_obj.write(cr, uid, [requisition_id], {'purchase_ids': [(6, 0, res.values())]}, context=context)
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id], 'requisition_id': requisition_id})
        self.message_post(cr, uid, ids, body=_("Draft Purchase Order created"), context=context)
        return res

procurement_order()

class res_users(osv.Model):
    _inherit = 'res.users'

    _columns = {
        'sign': fields.binary("Sign", help="This field holds the image used for the signature, limited to 1024x1024px."),
    }

res_users()

class hr_employee(osv.Model):
    _inherit = "hr.employee"

    _columns = {
        'absent': fields.boolean("Not in office"),
    }

hr_employee()

class product_order_series(osv.Model):
    _name = 'product.order.series'
    _description = ' Add Purchase Order series'
    _rec_name = 'code'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=32, required=True),
        'type': fields.selection([('indent', 'Indent'), ('purchase','Purchase')], 'Type', required=True),
        'seq_id': fields.many2one('ir.sequence', 'Sequence'),
        'seq_type_id': fields.many2one('ir.sequence.type', 'Sequence Type'),
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code,type)', 'The code of the product order series must be unique!')
    ]

    def create(self, cr, uid, vals, context=None):
        name = vals['name']
        prefix = vals['code']
        code = vals['type'] + vals['code']
        vals['seq_type_id'] = self.pool.get('ir.sequence.type').create(cr, uid, {'name': name, 'code': code}, context=context)
        seq = {
            'name': name,
            'implementation':'no_gap',
            'prefix': '%(year)s/'+prefix + "/",
            'suffix': '',
            'padding': 4,
            'number_increment': 1,
            'code': code
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        vals['seq_id'] = self.pool.get('ir.sequence').create(cr, uid, seq, context=context)
        return super(product_order_series, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        seq_obj = self.pool.get('ir.sequence')
        seq_type_obj = self.pool.get('ir.sequence.type')
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('code'):
            for series in self.browse(cr, uid, ids, context=context):
                seq_type_obj.write(cr, uid, [series.seq_type_id.id], {'code': series.type + vals.get('code')}, context=context)
                seq_obj.write(cr, uid, [series.seq_id.id], {'code': series.type + vals.get('code'), 'prefix': vals.get('code') + "/"}, context=context)
        return super(product_order_series, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        seq_ids = []
        seq_type_ids = []
        for series in self.browse(cr, uid, ids, context=context):
            if series.seq_id:
                seq_ids.append(series.seq_id.id)
            if series.seq_type_id:
                seq_type_ids.append(series.seq_type_id.id)
        self.pool.get('ir.sequence').unlink(cr, uid, seq_ids, context=context)
        self.pool.get('ir.sequence.type').unlink(cr, uid, seq_type_ids, context=context)
        return super(product_order_series, self).unlink(cr, uid, ids, context=context)

product_order_series()

class stock_location(osv.Model):
    _inherit = 'stock.location'

    _columns = {
        'seq_id': fields.many2one('ir.sequence', 'Sequence'),
        'seq_type_id': fields.many2one('ir.sequence.type', 'Sequence Type'),
        'maize_location': fields.boolean('Maize Location'),
        'manager_id': fields.many2one('hr.employee','Manager'),
    }

    def create(self, cr, uid, vals, context=None):
        if not vals.get('location_id', False) and vals.get('code', False):
            name = vals['name']
            code = vals['code']
            if vals.get('code') == '0**':
                prefix = '5'
                padding = 3
            else:
                prefix = vals.get('code')[0]
                padding = 4
            vals['seq_type_id'] = self.pool.get('ir.sequence.type').create(cr, uid, {'name': name, 'code': code}, context=context)
            seq = {
                'name': name,
                'implementation':'no_gap',
                'prefix': '%(year)s/'+prefix,
                'padding': padding,
                'number_increment': 1,
                'code': code
            }
            if 'company_id' in vals:
                seq['company_id'] = vals['company_id']
            vals['seq_id'] = self.pool.get('ir.sequence').create(cr, uid, seq, context=context)
        return super(stock_location, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        seq_obj = self.pool.get('ir.sequence')
        seq_type_obj = self.pool.get('ir.sequence.type')
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not vals.get('location_id', False) and vals.get('code', False):
            if vals.get('code') == '0**':
                prefix = '5'
                padding = 3
            else:
                prefix = vals.get('code')[0]
                padding = 4
            for location in self.browse(cr, uid, ids, context=context):
                if location.seq_type_id:
                    seq_type_obj.write(cr, uid, [location.seq_type_id.id], {'code': vals.get('code')}, context=context)
                if location.seq_id:
                    seq_obj.write(cr, uid, [location.seq_id.id], {'code': vals.get('code'), 'prefix': '%(year)s/'+prefix, 'padding': padding}, context=context)
        return super(stock_location, self).write(cr, uid, ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        seq_ids = []
        seq_type_ids = []
        for location in self.browse(cr, uid, ids, context=context):
            if location.seq_id:
                seq_ids.append(location.seq_id.id)
            if location.seq_type_id:
                seq_type_ids.append(location.seq_type_id.id)
        self.pool.get('ir.sequence').unlink(cr, uid, seq_ids, context=context)
        self.pool.get('ir.sequence.type').unlink(cr, uid, seq_type_ids, context=context)
        return super(stock_location, self).unlink(cr, uid, ids, context=context)

stock_location()

class stock_move(osv.Model):
    _inherit = 'stock.move'

    _columns = {
        'indent': fields.many2one('indent.indent', 'Indent'),
        'indentor': fields.many2one('res.users', 'Indentor'),
        'department_id': fields.many2one('stock.location', 'Department'),
    }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
