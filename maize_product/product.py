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

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp import netsvc

class stock_location(osv.Model):
    _inherit = 'stock.location'
    _rec_name = 'code'
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res   

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
        """
        Returns a list of tuples containing id, name, as internally it is called {def name_get}
        result format: {[(id, name), (id, name), ...]}

        @param cr: A database cursor
        @param user: ID of the user currently logged in
        @param name: name to search
        @param args: other arguments
        @param operator: default operator is 'ilike', it can be changed
        @param context: context arguments, like lang, time zone
        @param limit: Returns first 'n' ids of complete result, default is 80.

        @return: Returns a list of tuples containing id and name
        """
        if args is None:
            args = []
        ids = []
        if name:
            ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context=context)

    _columns = {
        'code': fields.char('Code', size=15),
        }
stock_location()

class account_analytic_account(osv.Model):
    _inherit = 'account.analytic.account'
    _rec_name = 'code'
    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of an project must be unique!')
    ]

account_analytic_account()

class product_major_group(osv.Model):
    _name = 'product.major.group'
    _description = ' Add Product major Code'
    _rec_name = 'code'
    _columns = {
        'code': fields.char('Code', size=15),
        'name': fields.char('Description', size=50),
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the product major group must be unique!')
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res      
product_major_group()

class product_sub_group(osv.Model):
    _name = 'product.sub.group'
    _description = ' Add Product sub Code'
    _rec_name = 'code'
    _columns = {
        'code': fields.char('Code', size=15),
        'name': fields.char('Description', size=50),
        'major_group_id':fields.many2one('product.major.group', 'Major Group'),
        }

    _sql_constraints = [
        ('code_uniq', 'unique (code,major_group_id)', 'The code of the product sub group must be unique!')
    ]

    def name_get(self, cr, uid, ids, context=None):
        if not len(ids):
            return []
        res = []
        for pckg in self.browse(cr, uid, ids, context=context):
            p_name = pckg.code and '[' + pckg.code + '] ' or ''
            p_name += pckg.name
            res.append((pckg.id,p_name))
        return res          
product_sub_group()

class product_product(osv.Model):
    _inherit = 'product.product'
    _order = 'id desc,default_code'

    def _get_product(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.product_id.id] = True
        return result.keys()

    def weighted_rate(self, cr, uid, ids, field_name, arg, context=None):
        stock_move_obj = self.pool.get('stock.move')
        product_obj = self.pool.get('product.product')
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id]={'weighted_rate': 0.0,'value_total': 0.0}
            receipt_qty = 0.0
            amount = 0.0
            move_ids = stock_move_obj.search(cr, uid, [('product_id', '=', product.id), ('type', '=', 'receipt'), ('state','=','done')], context=context)
            for move_obj in stock_move_obj.browse(cr, uid, move_ids, context=context):
                receipt_qty += move_obj.product_qty
                amount += move_obj.product_qty * move_obj.rate

            if receipt_qty > 0:
                res[product.id]['weighted_rate'] = amount / receipt_qty
                res[product.id]['value_total'] = amount
            else:
                res[product.id]['weighted_rate'] = 0.0
                res[product.id]['value_total'] = 0.0
        return res

    def last_supplier_code(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def last_po_year(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

#    def last_po_no(self, cr, uid, ids, field_name, arg, context=None):
#        res = {}
#        purchase_obj = self.pool.get('purchase.order')
#        purchase_line_obj = self.pool.get('purchase.order.line')
#        for order in self.browse(cr, uid, ids, context=context):
#            res[order.id] = {
#                'last_po_no': '',
#                'last_supplier_rate': '',
#            }
#            purchase_line_id = purchase_line_obj.search(cr, uid, [('product_id', '=', order.id)], context=context)
#            purchase_id = purchase_obj.search(cr, uid, [('order_line', 'in', purchase_line_id),('state', '=', 'approved')], context=context)
#            if purchase_id:
#                purchase_name = purchase_obj.read(cr, uid, purchase_id[0], ['name'], context)
#                line_id = purchase_line_obj.search(cr, uid, [('product_id', '=', order.id),('order_id', '=', purchase_id[0])], context=context)
#                line_qty = purchase_line_obj.read(cr, uid, line_id[0], ['price_unit'], context)['price_unit']
#                res[order.id]['last_po_no'] = purchase_id[0]
#                res[order.id]['last_supplier_rate'] = line_qty
#            else:
#                res[order.id]['last_po_no'] = False
#                res[order.id]['last_supplier_rate'] = 0.0
#        return res

    def cy_opening_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def cy_opening_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def cy_issue_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def cy_issue_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def last_po_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res

    def _merge_name(self, cr, uid, ids, name, arg, context=None):
        """
        @ Complete_name  = name + desc2 + desc3 + desc4
        """
        res = {}
        if context is None: context = {}
        for product in self.browse(cr, uid, ids, context=context):
            string = ''
            if product.name: string += product.name+' '
            if product.desc2: string += product.desc2+' '
            if product.desc3: string += product.desc3+' '
            if product.desc4: string += product.desc4+' '
            res[product.id] = string.strip()
        return res

    _columns = {
        'last_supplier_code': fields.many2one('res.partner', string='Last Supplier Code',readonly=True),
        'complete_name': fields.function(_merge_name,type="text", string='Complete Name',store=True),
        'last_po_year': fields.char('Last PO Year',size=256,readonly=True),
        'last_po_no': fields.many2one('purchase.order', 'Last PO No',readonly=True),
        'last_supplier_rate': fields.float('Last Supplier Rate',readonly=True),
        'last_recieve_date': fields.datetime('Last Receieve Date', readonly=True),
        'last_issue_date': fields.datetime('Last Issue Date', readonly=True),
        'cy_opening_qty': fields.function(cy_opening_qty, type='float', string='Current Year Opening Quantity'),
        'cy_opening_value': fields.function(cy_opening_value, type='float', string='Current Year Opening Value'),
        'last_recieve_qty': fields.float('Last Receieve Quantity', readonly=True),
        'last_recieve_value': fields.float('Last Receieve value', readonly=True),
        'last_issue_qty': fields.float('Last Issue Quantity', readonly=True),
        'last_issue_value': fields.float('Last Issue Value', readonly=True),
        'cy_issue_qty': fields.function(cy_issue_qty, type='float', string='Current Year Issue Quantity'),
        'cy_issue_value': fields.function(cy_issue_value, type='float', string='Current Year Issue Value'),
        'weighted_rate': fields.function(weighted_rate, type="float",multi="report", string='Weighted Rate',store={
            'stock.move':  (_get_product,['state'],10)},track_visibility='always'),
        'value_total': fields.function(weighted_rate, type="float",multi="report",string='Total value',store={
            'stock.move':  (_get_product,['state'],20)},track_visibility='always'),
        'last_po_date': fields.date('Last PO Date',readonly=True),
        'last_po_series': fields.many2one('product.order.series', 'Last PO Series',readonly=True),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'ex_chapter_desc': fields.text('EXCHAPTERDESCR',translate=True),
        'variance': fields.integer('Variance', help='Percentage that shows the actual difference between the ordered quantity and received one'),
        'item_type': fields.selection([('gp', 'GP')], 'Item Type'),
        'description': fields.char('Description', size=256),
        'desc2': fields.char('Description2', size=256),
        'desc3': fields.char('Description3', size=256),
        'desc4': fields.char('Description4', size=256),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'major_group_id': fields.many2one('product.major.group', 'Major Group'),
        'sub_group_id': fields.many2one('product.sub.group', 'Sub Group'),
        'location': fields.char('Location', size=256),
        #'state': fields.char('Location', size=256),
        'state': fields.selection([
            ('draft', 'Unconfirmed'),
            ('cancel', 'Cancelled'),
            ('confirm', 'Confirmed'),
            ('done', 'Approve')],
            'Status', readonly=True, required=True,
            track_visibility='onchange'),
        'min_qty': fields.related('orderpoint_ids', 'product_min_qty', type="float", relation="stock.warehouse.orderpoint", help="Minimum Qantity for this Product"),
        'max_qty': fields.related('orderpoint_ids', 'product_max_qty', type="float", relation="stock.warehouse.orderpoint", help="Maximum Qantity for this Product"),
        
        }

    _defaults = {
        'sale_ok':False,
        'type':'product',
        'purchase_requisition':True,
        'state':'draft',
    }

    def set_to_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirm'}, context=context)

    def set_to_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def set_to_approve(self, cr, uid, ids, context=None):
        obj_prod_categ=self.pool.get('product.category')
        obj_major_grp = self.pool.get('product.major.group')
        obj_sub_grp = self.pool.get('product.sub.group')
        default_code = '/'
        for record in self.browse(cr,uid,ids,context=context):
            categ_name = obj_prod_categ.browse(cr,uid,record.categ_id.id).name
            if categ_name == 'Local':
                categ_code ='01'
                categ_id = obj_prod_categ.search(cr,uid,[('name','=',categ_name)])
            else:
                categ_code ='02'
                categ_id = obj_prod_categ.search(cr,uid,[('name','=',categ_name)])
            major_group_code = obj_major_grp.browse(cr,uid,record.major_group_id and record.major_group_id.id).code or ''
            sub_group_code = obj_sub_grp.browse(cr,uid,record.sub_group_id and record.sub_group_id.id).code or ''
            
            major_id = obj_major_grp.search(cr,uid,[('code','=',major_group_code)])
            sub_id = obj_sub_grp.search(cr,uid,[('major_group_id','=',major_id and major_id[0] or False),('code','=',sub_group_code)])
            seq_id = self.search(cr,uid,[('categ_id','=',categ_id),('major_group_id','=',major_id and major_id[0] or False),('sub_group_id','=',sub_id and sub_id[0] or False)])
            seq_id.sort()
            product_code=1
            if record.type=='product' or record.type == 'service':
                if len(seq_id)>=2:
                    last_rec=self.browse(cr,uid,seq_id[-2])
                    if int(last_rec.default_code[6:9]) == 999:
                        raise osv.except_osv(_('Warning!'), _('Maximum Number reached of this major group'))
                    product_code = int(last_rec.default_code[6:9])+1
                    default_code = categ_code+major_group_code+sub_group_code+"%03d"%(product_code)
                else:
                    default_code = categ_code+major_group_code+sub_group_code+"001"
        return self.write(cr, uid, ids, {'state': 'done','default_code':default_code}, context=context)

    def set_to_reject(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel','active':False}, context=context)

product_product()

class stock_move(osv.Model):
    _inherit = "stock.move"
    
    def action_done(self, cr, uid, ids, context=None):
        res = super(stock_move,self).action_done(cr, uid, ids, context=context)
        product_obj = self.pool.get('product.product')
        for move in self.browse(cr, uid, ids, context=context):
            if move.type == 'internal':
                product_obj.write(cr, uid, move.product_id.id, {'last_issue_date': move.create_date, 'last_issue_qty': move.product_qty, 'last_issue_value': (move.product_qty * move.product_id.standard_price)})
            elif move.type == 'in':
                product_obj.write(cr, uid, move.product_id.id, {'last_recieve_date': move.create_date, 'last_recieve_qty': move.product_qty, 'last_recieve_value': (move.product_qty * (move.purchase_line_id and move.purchase_line_id.price_unit or 0.0))})
        return res
