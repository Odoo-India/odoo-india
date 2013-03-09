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
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import amount_to_text_en as text
from openerp import netsvc
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class indent_indent(osv.Model):
    _name = 'indent.indent'
    _description = 'Indent'
    _inherit = ['mail.thread']
    _track = {
        'state': {
            'indent.mt_indent_confirmed': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'indent.mt_indent_waiting_approval': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'waiting_approval',
            'indent.mt_indent_inprogress': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'inprogress',
            'indent.mt_indent_received': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'received',
            'indent.mt_indent_rejected': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'reject'
        },
    }

    def _check_po_done(self, cr, uid, ids, field_name, arg=False, context=None):
        res = {}
        requisition_obj = self.pool.get('purchase.requisition')
        req_ids = requisition_obj.search(cr, uid, [('indent_id', 'in', ids)])
        if req_ids:
            for req_id in requisition_obj.browse(cr, uid, req_ids):
                po_done = False
                if req_id.state == 'done':
                    po_done = True
                res[ids[0]] = po_done
        else:
            res[ids[0]] = False
        return res

    _columns = {
        'name': fields.char('Indent #', size=256, required=True, track_visibility='always'),
        'indent_date': fields.datetime('Indent Date', required=True),
        'required_date': fields.datetime('Required Date', required=True),
        'indentor_id': fields.many2one('res.users', 'Indentor', required=True, track_visibility='always'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'employee_department_id': fields.related('employee_id', 'department_id', type='many2one', relation='hr.department', string='Employee Department', store=True),
        'department_id': fields.many2one('stock.location', 'Department', required=True, track_visibility='onchange'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Project', ondelete="cascade", track_visibility='onchange'),
        'requirement': fields.selection([('ordinary','Ordinary'), ('urgent','Urgent')],'Requirement', required=True, track_visibility='onchange'),
        'type': fields.selection([('new','New'), ('existing','Existing')],'Indent Type', required=True, track_visibility='onchange'),
        'product_lines': fields.one2many('indent.product.lines', 'indent_id', 'Products'),
        'picking_id': fields.many2one('stock.picking','Picking'),
        'description': fields.text('Item Description'),
        'company_id': fields.many2one('res.company', 'Company'),
        'indent_authority_ids': fields.one2many('document.authority.instance', 'indent_id', 'Authority'),
        'state':fields.selection([('draft','Draft'), ('confirm','Confirm'), ('waiting_approval','Waiting For Approval'), ('inprogress','Inprogress'), ('received','Received'), ('reject','Rejected')], 'State', readonly=True, track_visibility='onchange'),
        'purchase_done': fields.function(_check_po_done, type='boolean', string="Check Purchase Done"),
        'purchase_count': fields.boolean('Puchase Done', help="Check box True means the Purchase Order is done for this Indent"),
    }

    def _default_employee_id(self, cr, uid, context=None):
        employees = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if not employees:
            raise osv.except_osv(_("Warning !"),_('You must define an employee and assign the related user to that employee.'))
        return employees and employees[0] or False

    def _default_stock_location(self, cr, uid, context=None):
        stock_location = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'stock_location_stock')
        return stock_location.id

    _defaults = {
        'state': 'draft',
        'name': lambda obj, cr, uid, context:obj.pool.get('ir.sequence').get(cr, uid, 'indent.indent'),
        'indent_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'required_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'indentor_id': lambda self, cr, uid, context: uid,
        'employee_id': _default_employee_id,
        'department_id': _default_stock_location,
        'requirement': 'ordinary',
        'type': 'new',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'indent.indent', context=c)
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'name': self.pool.get('ir.sequence').get(cr, uid, 'indent.indent'),
            'indent_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'required_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'product_lines': [],
            'picking_id': False,
            'indent_authority_ids': [],
            'state': 'draft',
        })
        return super(indent_indent, self).copy(cr, uid, id, default, context=context)

    def _create_hierarchy(self, cr, uid, indent, emp, priority, context=None):
        if not emp.coach_id and not emp.coach_id.user_id:
            return True
        else:
            self.pool.get('document.authority.instance').create(cr, uid, {'name': emp.coach_id.user_id.id, 'document': 'indent', 'indent_id': indent.id, 'priority': priority}, context=context)
            priority -= 2
            return self._create_hierarchy(cr, uid, indent, emp.coach_id, priority=priority, context=context)

    def indent_confirm(self, cr, uid, ids, context=None):
        document_authority_instance_obj = self.pool.get('document.authority.instance')
        for indent in self.browse(cr, uid, ids, context=context): 
            if not indent.product_lines:
                raise osv.except_osv(_("Warning !"),_('You cannot confirm an indent which has no line.'))
            if indent.employee_id and indent.employee_id.user_id:
                document_authority_instance_obj.create(cr, uid, {'name': indent.employee_id.user_id.id, 'document': 'indent', 'indent_id': indent.id, 'priority': 10}, context=context)
            self._create_hierarchy(cr, uid, indent, indent.employee_id, priority=8, context=context)
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return True

    def action_picking_create(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        picking_id = False
        indent = self.browse(cr, uid, ids[0], context=context)
        if indent.product_lines:
            picking_id = self._create_pickings_and_procurements(cr, uid, indent, indent.product_lines, None, context=context)
        self.write(cr, uid, ids, {'picking_id': picking_id, 'state' : 'inprogress'}, context=context)
        return picking_id

    def check_approval(self, cr, uid, ids):
        document_authority_instance_obj = self.pool.get('document.authority.instance')
        for indent in self.browse(cr, uid, ids):
            authorities = [(authority.id, authority.name.id, authority.priority, authority.state, authority.name.name) for authority in indent.indent_authority_ids]
            sort_authorities = sorted(authorities, key=lambda element: (element[2]))
            count = 0
            for authority in sort_authorities:
                count += 1
                if authority[1] == uid:
                    if authority[3] == 'approve':
                        raise osv.except_osv(_("Warning !"),_('You have already approved an indent.'))
                    write_ids = [(auth[0], auth[3]) for auth in sort_authorities][count:]
                    document_authority_instance_obj.write(cr, uid, [authority[0]], {'state': 'approve'})
                    for write_id in write_ids:
                        desc = document_authority_instance_obj.browse(cr, uid, write_id[0]).description
                        description = 'Approved by higher authority - %s' %(authority[4],)
                        if desc:
                            description = 'Approved by higher authority - %s' %(authority[4],) + '\n' + desc
                        document_authority_instance_obj.write(cr, uid, [write_id[0]], {'description': description})
                    break

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
            for authority in sort_authorities:
                count += 1
                if authority[1] == uid:
                    if authority[3] == 'reject':
                        raise osv.except_osv(_("Warning !"),_('You have already rejected an indent.'))
                    write_ids = [(auth[0], auth[3]) for auth in sort_authorities][count:]
                    document_authority_instance_obj.write(cr, uid, [authority[0]], {'state': 'reject'})
                    for write_id in write_ids:
                        desc = document_authority_instance_obj.browse(cr, uid, write_id[0]).description
                        description = 'Rejected by higher authority - %s' %(authority[4],)
                        if desc:
                            description = 'Rejected by higher authority - %s' %(authority[4],) + '\n' + desc
                        document_authority_instance_obj.write(cr, uid, [write_id[0]], {'description': description})
                    break

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

    def _prepare_indent_line_move(self, cr, uid, indent, line, picking_id, date_planned, context=None):
        location_id = self._default_stock_location(cr, uid, context=context)
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
        location_id = self._default_stock_location(cr, uid, context=context)
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

    def process_purchase_order(self,cr,uid,ids,context):
        obj_purchase_order = self.pool.get('purchase.order')
        wf_service = netsvc.LocalService("workflow")
        for indent in self.browse(cr,uid,ids,context):
            if indent.purchase_count ==  True:
                raise osv.except_osv(_('Warning!'),_("Purchase Order is already process !"))
            po_grp_partners = obj_purchase_order.read_group(cr, uid, [('indent_id', '=', indent.id),('state', '=', 'approved')], ['partner_id'], ['partner_id'])
            for po_grp_partner in po_grp_partners:
                if po_grp_partner['partner_id_count'] > 1:
                    po_to_merge = obj_purchase_order.search(cr, uid, [('indent_id', '=', indent.id),('state', '=', 'approved'),('partner_id', '=', po_grp_partner['partner_id'][0])])
                    obj_purchase_order.action_cancel(cr,uid,po_to_merge,context)
                    obj_purchase_order.action_cancel_draft(cr,uid,po_to_merge,context)
                    po_merged_id = obj_purchase_order.do_merge(cr,uid,po_to_merge,context).keys()[0]
                    order = obj_purchase_order.browse(cr,uid,po_merged_id,context)
                    today = order.date_order
                    year = datetime.datetime.today().year
                    month = datetime.datetime.today().month
                    if month < 4:
                        po_year=str(datetime.datetime.today().year-1)+'-'+str(datetime.datetime.today().year)
                    else:
                        po_year=str(datetime.datetime.today().year)+'-'+str(datetime.datetime.today().year+1)
                    for line in order.order_line:
                        self.pool.get('product.product').write(cr,uid,line.product_id.id,{
                                                                      'last_supplier_rate': line.price_unit,
                                                                      'last_po_no':order.id,
                                                                      'last_po_series':order.po_series_id.id,
                                                                      'last_supplier_code':order.partner_id.id,
                                                                      'last_po_date':order.date_order,
                                                                      'last_po_year':po_year
                                                                  },context=context)
                    obj_purchase_order.write(cr,uid,po_merged_id,{'indentor_id':indent.indentor_id.id,'indent_date':indent.indent_date,'indent_id':indent.id,'origin':indent.name})
                    wf_service.trg_validate(uid, 'purchase.order', po_merged_id, 'purchase_confirm', cr)
                    wf_service.trg_validate(uid, 'purchase.order', po_merged_id, 'purchase_approve', cr)
            self.write(cr, uid, indent.id, {'purchase_count': True}, context=context)
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
        'virtual_available': fields.float('Forecasted Qty'),
        'name': fields.text('Purpose', required=True),
        'specification': fields.text('Item Specification'),
    }

    def _get_uom_id(self, cr, uid, *args):
        result = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_unit')
        return result and result[1] or False

    _defaults = {
        'product_uom' : _get_uom_id,
        'product_uom_qty': 1,
        'product_uos_qty': 1,
        'type': 'make_to_order',
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

        result['qty_available'] = product_obj.qty_available
        result['virtual_available'] = product_obj.virtual_available
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
        'document': fields.selection([('indent','Indent'), ('order','Purchase Order')], 'Document', required=True),
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
        'state': fields.selection([
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('auto', 'Waiting Another Operation'),
            ('confirmed', 'Waiting Availability'),
            ('assigned', 'Ready to Transfer'),
            ('done', 'Transferred'),
            ('cancel', 'Cancelled'),
            ], 'Status', readonly=True, select=True, track_visibility='onchange', help="""
            * Draft: not confirmed yet and will not be scheduled until confirmed\n
            * Approved: waiting for manager approval to proceed further\n
            * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
            * Waiting Availability: still waiting for the availability of products\n
            * Ready to Transfer: products reserved, simply waiting for confirmation.\n
            * Transferred: has been processed, can't be modified or cancelled anymore\n
            * Cancelled: has been cancelled, can't be confirmed anymore"""
        ),
    }

    def check_manager_approval(self, cr, uid, ids):
        indent = self.browse(cr, uid, ids[0]).indent_id
        manager = indent and indent.employee_department_id and indent.employee_department_id.manager_id and indent.employee_department_id.manager_id.user_id and indent.employee_department_id.manager_id.user_id.id or False
        if manager and manager == uid:
            return True
        elif manager and manager != uid:
            return False
        return True

stock_picking()

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
    }

    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        res = super(purchase_requisition, self).make_purchase_order(cr, uid, ids, partner_id, context=context)
        origin = self.browse(cr, uid, ids[0], context).origin
        if origin:
            self.pool.get('purchase.order').write(cr, uid, res.values(), {'origin': origin}, context=context)
        return res

purchase_requisition()

class procurement_order(osv.osv):
    _inherit = 'procurement.order'

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

            name = product.partner_ref
            if product.description_purchase:
                name += '\n'+ product.description_purchase
            line_vals = {
                'name': name,
                'product_qty': qty,
                'product_id': procurement.product_id.id,
                'product_uom': uom_id,
                'price_unit': price or 0.0,
                'date_planned': schedule_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'move_dest_id': res_id,
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
