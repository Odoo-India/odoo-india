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

class product_order_series(osv.Model):
    _name = 'product.order.series'
    _description = ' Add Purchase Order series'
    _rec_name = 'code'
    
    _columns = {
        'code': fields.char('Series', size=15),
        'name': fields.char('Description', size=50),
        }
product_order_series()

class product_major_group(osv.Model):
    _name = 'product.major.group'
    _description = ' Add Product major Code'
    _columns = {
        'code': fields.char('Code', size=15),
        'name': fields.char('Description', size=50),
        }
product_major_group()

class product_sub_group(osv.Model):
    _name = 'product.sub.group'
    _description = ' Add Product major Code'
    _columns = {
        'code': fields.char('Code', size=15),
        'name': fields.char('Description', size=50),
        'major_group_id':fields.many2one('product.major.group', 'Major Group'),
        }
product_sub_group()

class product_product(osv.Model):
    _inherit = 'product.product'
    
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
    
    def last_po_no(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'last_po_no': '',
                'last_supplier_rate': '',
            }
            purchase_line_id = purchase_line_obj.search(cr, uid, [('product_id', '=', order.id)], context=context)
            purchase_id = purchase_obj.search(cr, uid, [('order_line', 'in', purchase_line_id),('state', '=', 'approved')], context=context)
            if purchase_id:
                purchase_name = purchase_obj.read(cr, uid, purchase_id[0], ['name'], context)
                line_id = purchase_line_obj.search(cr, uid, [('product_id', '=', order.id),('order_id', '=', purchase_id[0])], context=context)
                line_qty = purchase_line_obj.read(cr, uid, line_id[0], ['price_unit'], context)['price_unit']
                res[order.id]['last_po_no'] = purchase_id[0]
                res[order.id]['last_supplier_rate'] = line_qty
            else:
                res[order.id]['last_po_no'] = False
                res[order.id]['last_supplier_rate'] = 0.0
        return res
    
    def last_recieve_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res
    
    def last_issue_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res
    
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
    
    def last_recieve_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res
    
    def last_recieve_value(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res
    
    def last_issue_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = ''
        return res
    
    def last_issue_value(self, cr, uid, ids, field_name, arg, context=None):
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
    
    
    _columns = {
        'last_supplier_code': fields.function(last_supplier_code, type='char', string='Last Supplier Code'),
        'last_po_year': fields.function(last_po_year, type='date', string='Last PO Year'),
        'last_po_no': fields.function(last_po_no, type='many2one', relation='purchase.order', multi='po',string='Last PO No'),
        'last_supplier_rate': fields.function(last_po_no, type='float', multi='po',string='Last Supplier Rate'),
        'last_recieve_date': fields.function(last_recieve_date, type='date', string='Last Receieve Date'),
        'last_issue_date': fields.function(last_issue_date, type='date', string='Last Issue Date'),
        'cy_opening_qty': fields.function(cy_opening_qty, type='float', string='Current Year Opening Quantity'),
        'cy_opening_value': fields.function(cy_opening_value, type='float', string='Current Year Opening Value'),
        'last_recieve_qty': fields.function(last_recieve_qty, type='float', string='Last Receieve Quantity'),
        'last_recieve_value': fields.function(last_recieve_value, type='float', string='Last Receieve value'),
        'last_issue_qty': fields.function(last_issue_qty, type='float', string='Last Issue Quantity'),
        'last_issue_value': fields.function(last_issue_value, type='float', string='Last Issue Value'),
        'cy_issue_qty': fields.function(cy_issue_qty, type='float', string='Current Year Issue Quantity'),
        'cy_issue_value': fields.function(cy_issue_value, type='float', string='Current Year Issue Value'),
        'last_po_date': fields.function(last_po_date, type='date', string='Last PO Date'),
        'last_po_series': fields.many2one('product.order.series', 'Last PO Series'),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'ex_chapter_desc': fields.text('EXCHAPTERDESCR',translate=True),
        'variance': fields.integer('Variance', help='Percentage that shows the actual difference between the ordered quantity and received one'),
        'status': fields.integer('Status', help='There is a report that is generated from this status for store people monthly'),
        'item_type': fields.selection([('gp', 'GP'), ('im' , 'IM')], 'Item Type'),
        'description': fields.char('Description', size=256),
        'desc2': fields.char('Description2', size=256),
        'desc3': fields.char('Description3', size=256),
        'desc4': fields.char('Description4', size=256),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'ex_chapter': fields.char('EXCHAPTER', size=30, translate=True),
        'major_group_id': fields.many2one('product.major.group', 'Major Group',required=True),
        'sub_group_id': fields.many2one('product.sub.group', 'Sub Group',required=True),
        'item_code': fields.char('Item Code', size=30),
        }
    _defaults = {
                'sale_ok':False,
                'type':'product',
                }
#    def create(self, cr, uid, vals, context=None):
#        obj_prod_categ=self.pool.get('product.category')
#        obj_major_grp = self.pool.get('product.major.group')
#        obj_sub_grp = self.pool.get('product.sub.group')
#        if vals.get('item_code','/')=='/':
#            categ_name = obj_prod_categ.browse(cr,uid,vals['categ_id']).name
#            if categ_name == 'Local':
#                categ_code ='01'
#            else:
#                 categ_code ='02'
#            major_group_code = obj_major_grp.browse(cr,uid,vals['major_group_id']) and  obj_major_grp.browse(cr,uid,vals['major_group_id']).code or ''
#            sub_group_code = obj_sub_grp.browse(cr,uid,vals['sub_group_id']) and obj_sub_grp.browse(cr,uid,vals['sub_group_id']).code or ''
#            
#            vals['item_code'] = categ_code+major_group_code+sub_group_code+self.pool.get('ir.sequence').get(cr, uid, 'product.product') or '/'
#        product =  super(product_product, self).create(cr, uid, vals, context=context)
#        return product
    
#    def write(self, cr, uid, ids,vals, context=None):
#        obj_prod_categ=self.pool.get('product.category')
#        obj_major_grp = self.pool.get('product.major.group')
#        obj_sub_grp = self.pool.get('product.sub.group')
#        record = self.browse(cr,uid,ids)[0]
#        if 'categ_id' in vals:
#            categ_name = obj_prod_categ.browse(cr,uid,vals['categ_id']).name
#        else:
#            categ_name = record.categ_id.name
#            
#        if categ_name == 'Local':
#            categ_code ='01'
#        else:
#             categ_code ='02'    
#             
#        if 'major_group_id' in vals:
#            major_group_code = obj_major_grp.browse(cr,uid,vals['major_group_id']).code
#        else:
#            major_group_code = record.major_group_id.code
#            
#        if 'sub_group_id' in vals:
#            sub_group_code = obj_sub_grp.browse(cr,uid,vals['sub_group_id']).code
#        else:
#            sub_group_code = record.sub_group_id.code              
#
#        vals['item_code'] = categ_code+major_group_code+sub_group_code+self.pool.get('ir.sequence').get(cr, uid, 'product.product') or '/'
#        product =  super(product_product, self).write(cr, uid, ids, vals, context=context)
#        return product    
product_product()
