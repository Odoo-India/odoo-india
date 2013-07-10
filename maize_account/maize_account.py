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

class account_tax(osv.Model):
    _name = 'account.tax'
    _inherit = 'account.tax'
    _columns = {
        'tax_type': fields.selection(
        [('excise', 'Excise'),
         ('cess', 'Education Cess'),
         ('hedu_cess', 'Higher Education Cess'),
         ('vat', 'VAT'),
         ('cst', 'CST'),
         ('service', 'Service'),
         ('other', 'Other'),
        ], 'Tax Category', required=True)
    }

    def onchange_tax_type(self, cr, uid, ids, name, tax_type=False, context=None):
        record = self.browse(cr, uid, ids, context)
        result = {}
        vals = []
        if tax_type == 'excise':
            
            vals = [{'name':'Edu.cess 2% on '+name,
                    'tax_type':'excise',
                    'sequence':1,
                    'type':'percent',
                    'amount':0.02,
                    'include_base_amount':False,
                    'tax_type':'cess',
                    'type_tax_use':'all',
                   },{'name':'Edu.cess 1% on '+name,
                    'tax_type':'excise',
                    'sequence':1,
                    'type':'percent',
                    'amount':0.01,
                    'include_base_amount':False,
                    'type_tax_use':'all',
                    'tax_type':'cess',
                    }]
        result['child_ids'] = vals
        result['include_base_amount'] = True
        return {'value': result}
    
    def _unit_compute(self, cr, uid, taxes, price_unit, product=None, partner=None, quantity=0):
        taxes = self._applicable(cr, uid, taxes, price_unit , product, partner)
        res = []
        cur_price_unit = price_unit
        for tax in taxes:
            # we compute the amount for the current tax object and append it to the result
            data = {'id':tax.id,
                    'name':tax.description and tax.description + " - " + tax.name or tax.name,
                    'account_collected_id':tax.account_collected_id.id,
                    'account_paid_id':tax.account_paid_id.id,
                    'account_analytic_collected_id': tax.account_analytic_collected_id.id,
                    'account_analytic_paid_id': tax.account_analytic_paid_id.id,
                    'base_code_id': tax.base_code_id.id,
                    'ref_base_code_id': tax.ref_base_code_id.id,
                    'sequence': tax.sequence,
                    'base_sign': tax.base_sign,
                    'tax_sign': tax.tax_sign,
                    'ref_base_sign': tax.ref_base_sign,
                    'ref_tax_sign': tax.ref_tax_sign,
                    'price_unit': cur_price_unit,
                    'tax_code_id': tax.tax_code_id.id,
                    'ref_tax_code_id': tax.ref_tax_code_id.id,
                    'include_base_amount': tax.include_base_amount,
                    'parent_id':tax.parent_id
            }
            res.append(data)
            if tax.type == 'percent':
                amount = cur_price_unit * tax.amount
                data['amount'] = amount

            elif tax.type == 'fixed':
                data['amount'] = tax.amount
                data['tax_amount'] = quantity
                # data['amount'] = quantity
            elif tax.type == 'code':
                localdict = {'price_unit':cur_price_unit, 'product':product, 'partner':partner}
                exec tax.python_compute in localdict
                amount = localdict['result']
                data['amount'] = amount
            elif tax.type == 'balance':
                data['amount'] = cur_price_unit - reduce(lambda x, y: y.get('amount', 0.0) + x, res, 0.0)
                data['balance'] = cur_price_unit

            amount2 = data.get('amount', 0.0)
            if tax.child_ids:
                if tax.child_depend:
                    latest = res.pop()
                amount = amount2
                child_tax = self._unit_compute(cr, uid, tax.child_ids, amount, product, partner, quantity)
                # Add Parent reference in child dictionary of tax so that we can inlcude tha amount of child ...
                for ctax in child_tax:
                    ctax['parent_tax'] = tax.id
                
                res.extend(child_tax)
                if tax.child_depend:
                    for r in res:
                        for name in ('base', 'ref_base'):
                            if latest[name + '_code_id'] and latest[name + '_sign'] and not r[name + '_code_id']:
                                r[name + '_code_id'] = latest[name + '_code_id']
                                r[name + '_sign'] = latest[name + '_sign']
                                r['price_unit'] = latest['price_unit']
                                latest[name + '_code_id'] = False
                        for name in ('tax', 'ref_tax'):
                            if latest[name + '_code_id'] and latest[name + '_sign'] and not r[name + '_code_id']:
                                r[name + '_code_id'] = latest[name + '_code_id']
                                r[name + '_sign'] = latest[name + '_sign']
                                r['amount'] = data['amount']
                                latest[name + '_code_id'] = False
            if tax.include_base_amount:
                cur_price_unit += amount2
                # Check for Child tax addition. If Tax has childrens and they have also set include in base amount we will add it for next tax calculation...
                for r in res:
                    if 'parent_tax' in r and r['parent_tax'] == tax.id:
                        cur_price_unit += r['amount']
        return res

account_tax()

class account_invoice_tax(osv.osv):
    _inherit = 'account.invoice.tax'

    _columns = {
        'tax_categ': fields.selection(
        [('excise', 'Excise'),
         ('cess', 'Cess'),
         ('hedu_cess', 'Higher Education Cess'),
         ('vat', 'VAT'),
         ('cst', 'CST'),
         ('other', 'Other'),
         ('service', 'Service'),
        ], 'Tax Category')
    }

    _defaults = {
        'tax_categ': 'other',
    }

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        for line in inv.invoice_line:
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, (line.price_unit) * ((1 - (line.discount or 0.0) / 100.0)), line.quantity, line.product_id, inv.partner_id)['taxes']:
                tax_id = tax['id']
                val = {}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity'])
                val['tax_categ'] = tax_obj.browse(cr, uid, tax_id, context=context).tax_type
                if inv.type in ('out_invoice', 'in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['base'] * tax['ref_base_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['tax_amount'] = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, val['amount'] * tax['ref_tax_sign'], context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')}, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']
                key = (val['tax_code_id'], val['base_code_id'], val['account_id'], val['account_analytic_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    pass
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']
        
        for t in tax_grouped.values():
            t['base'] = cur_obj.round(cr, uid, cur, t['base'])
            t['amount'] = cur_obj.round(cr, uid, cur, t['amount'])
            t['base_amount'] = cur_obj.round(cr, uid, cur, t['base_amount'])
            t['tax_amount'] = cur_obj.round(cr, uid, cur, t['tax_amount'])
        return tax_grouped

class account_invoice(osv.Model):
    _inherit = "account.invoice"

    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'bill_amount': 0.0,
                'net_amount': 0.0,
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] + invoice.freight + invoice.insurance + invoice.other_charges

            res[invoice.id]['bill_amount'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] + invoice.freight + \
                invoice.package_and_forwording + invoice.insurance + invoice.loading_charges + invoice.inspection_charges + invoice.delivery_charges \
                + invoice.other_charges - invoice.rounding_shortage

            res[invoice.id]['net_amount'] = res[invoice.id]['bill_amount'] - (invoice.debit_note_amount + invoice.advance_amount + invoice.retention_amount) 
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
        'freight': fields.float('Freight'),
        'other_charges': fields.float('Other Charges'),
        'insurance': fields.float('Insurance'),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'freight', 'insurance', 'other_charges', 'package_and_forwording', 'loading_charges', 'inspection_charges', 'delivery_charges', 'rounding_shortage'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'freight', 'insurance', 'other_charges'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'freight', 'insurance', 'other_charges', 'package_and_forwording', 'loading_charges', 'inspection_charges', 'delivery_charges', 'rounding_shortage'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'bill_amount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Bill Amount',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'freight', 'package_and_forwording', 'insurance', 'loading_charges', 'inspection_charges', 'delivery_charges', 'other_charges', 'rounding_shortage'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'carting':fields.selection([('nothing', 'Nothing')], 'Carting'),
        'package_and_forwording': fields.float('Packing'),
        'loading_charges': fields.float('Loading Charges'),
        'inspection_charges': fields.float('Inspection Charges'),
        'delivery_charges': fields.float('Delivery Charges'),
        'rounding_shortage': fields.float('Rounding Shortage'),
        'vat_amount': fields.float('VAT Amount'),
        'additional_amount': fields.float('Additional Tax'),
        'debit_note_amount': fields.float('Debit Note Amount'),
        'advance_amount': fields.float('Advance Amount'),
        'retention_amount': fields.float('Retention Amount'),
        'net_amount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Net Amount', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line', 'freight', 'package_and_forwording', 'insurance', 'loading_charges', 'inspection_charges', 'delivery_charges', 'other_charges', 'rounding_shortage', 'debit_note_amount', 'advance_amount', 'retention_amount'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'account_code': fields.many2one('account.account', 'Account Code'),
        'st_code':fields.selection([('nothing', 'Nothing')], 'S.T. Code'),
        'due_date': fields.date('Due Date'),
        'c_form':fields.selection([('nothing', 'Nothing')], 'C Form'),
    }
account_invoice()
