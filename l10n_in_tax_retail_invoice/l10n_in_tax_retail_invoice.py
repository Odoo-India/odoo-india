# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2013 Tiny SPRL (<http://tiny.be>).
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
from lxml import etree

from openerp.osv import fields, osv
from tools.amount_to_text_en import amount_to_text
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp
from openerp import tools

class product_category(osv.osv):
    
    _inherit = "product.category"
    
    _columns = {
        'hsn_classification': fields.char('Tariff/HSN Classification'),
    }
    
class product_product(osv.osv):
    
    _inherit = "product.product"
    
    def _check_packing_cost_allowed(self, cr, uid, ids, name, args, context=None):
        res = {}
        res_company = self.pool.get('res.company')
        for id in ids:
            packing_cost_allowed = res_company.browse(cr, uid, uid, context=context).packing_cost
            res[id] = packing_cost_allowed
        return res
    
    def _default_check_packing_cost_allowed(self, cr, uid, ids, context=None):
        res_company = self.pool.get('res.company')
        packing_cost_allowed = res_company.browse(cr, uid, uid, context=context).packing_cost
        return packing_cost_allowed
    
    _columns = {
        'packing_cost_type': fields.selection([
            ('fixed', 'Fixed'),
            ('percentage', 'Percentage'),
            ], 'Packing Cost Type'),
        'packing_fixed': fields.float('Packing Cost Amount'),
        'packing_percent': fields.float('Packing Cost Percentage', help='Give % in range of 0-100'),
        'packing_cost_allowed': fields.function(_check_packing_cost_allowed, string='Packing Cost Allowed', type='boolean')
    }
    
    _defaults = {
         'packing_cost_allowed': _default_check_packing_cost_allowed,
         'packing_cost_type': 'percentage',
     }
    
class res_partner(osv.osv):
    
    _inherit = "res.partner"
    
    def _check_dealers_discount_allowed(self, cr, uid, ids, name, args, context=None):
        res = {}
        res_company = self.pool.get('res.company')
        for id in ids:
            dealers_discount_allowed = res_company.browse(cr, uid, uid, context=context).dealers_discount
            res[id] = dealers_discount_allowed
        return res
    
    def _default_check_dealers_discount_allowed(self, cr, uid, ids, context=None):
        res_company = self.pool.get('res.company')
        dealers_discount_allowed = res_company.browse(cr, uid, uid, context=context).dealers_discount
        return dealers_discount_allowed
    
    _columns = {
        'tin_no' : fields.char('TIN', size=32, help="Tax Identification Number"),
        'cst_no' : fields.char('CST', size=32, help='Central Sales Tax Number of Customer'),
        'pan_no' : fields.char('PAN', size=32, help="Permanent Account Number"),
        'tin_date' : fields.date('TIN Date', help="Tax Identification Number Date"),
        'cst_date' : fields.date('CST Date', help="Central Sales Tax Number Date"),
        'dealer_id': fields.many2one('res.partner', 'Dealer'),
        'dealers_discount_allowed': fields.function(_check_dealers_discount_allowed, string='Dealers Discount Allowed', type='boolean'),
        'village_taluka': fields.char('Village', size=32),
    }
    
    _defaults = {
         'dealers_discount_allowed': _default_check_dealers_discount_allowed,
    }
    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct dealer_id from res_partner where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True

    _constraints = [
        (_check_recursion, 'Error ! You cannot create recursive dealers.', ['dealer_id'])
    ]
    
    def _display_address(self, cr, uid, address, without_company=False, context=None):

        '''
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.

        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        '''

        # get the information that will be injected into the display format
        # get the address format
        address_format = address.country_id and address.country_id.address_format or \
              "%(street)s\n%(street2)s\n%(city)s %(state_code)s %(zip)s\n%(country_name)s"
        args = {
            'state_code': address.state_id and address.state_id.code or '',
            'state_name': address.state_id and address.state_id.name or '',
            'country_code': address.country_id and address.country_id.code or '',
            'country_name': address.country_id and address.country_id.name or '',
            'company_name': address.parent_id and address.parent_id.name or '',
            'village_taluka': address.village_taluka or '',
        }
        address_field = ['title', 'street', 'street2', 'zip', 'city', 'village_taluka']
        for field in address_field :
            args[field] = getattr(address, field) or ''
        if without_company:
            args['company_name'] = ''
        elif address.parent_id:
            address_format = '%(company_name)s\n' + address_format
        return address_format % args
    
class sale_order(osv.osv):
    
    _inherit = "sale.order"
    
    def _get_pack_total(self, cursor, user, ids, name, arg, context=None):
        res = {}
        tot_diff = 0.0
        for sale in self.browse(cursor, user, ids, context=context):
            tot_diff = 0.0
            for line in sale.order_line:
                tot_diff += line.packing_amount  # Need to check if packing cost apply by qty sold? 
            res[sale.id] = tot_diff
        return res
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'invoice_id':False,
        })
        return super(sale_order, self).copy(cr, uid, id, default, context=context)
    
    def _amount_line_tax(self, cr, uid, line, context=None):
        sale_order_line_obj = self.pool.get('sale.order.line')
        packing_cost_allowed = sale_order_line_obj.browse(cr, uid, line.id, context=context).order_id.company_id.packing_cost
        if packing_cost_allowed:
            val = 0.0
            for c in self.pool.get('account.tax').compute_all(cr, uid, line.tax_id, (line.price_unit + line.packing_amount) * (1 - (line.discount or 0.0) / 100.0), line.product_uom_qty, line.product_id, line.order_id.partner_id)['taxes']:
                val += c.get('amount', 0.0)
            return val
        return super(sale_order, self)._amount_line_tax(cr, uid, line, context=context)
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        res = super(sale_order, self.pool.get('sale.order'))._get_order(cr, uid, ids, context=context)
        return res
    
    def _get_difference(self, cursor, user, ids, name, arg, context=None):
        res = {}
        tot_diff = 0.0
        for sale in self.browse(cursor, user, ids):
            tot_diff = 0.0
            for line in sale.order_line:
                if line.lst_price:
                    tot_diff += (line.price_unit - line.lst_price) * line.product_uom_qty
#                tot_diff = tot_diff - line.packing_amount # Need to check if packing cost apply by qty sold? 
            res[sale.id] = tot_diff
        return res
    
    def _get_qty_total(self, cr, uid, ids):
        res = {}
        qty = 0.0
        for order in self.browse(cr, uid, ids):
            for line in order.order_line:
                qty += line.product_uom_qty
            res[order.id] = qty
        return res
        
    _columns = {
        'contact_id': fields.many2one('res.partner', 'Contact'),
        'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', required=True, help="Delivery address for current sales order."),
        'packing_total': fields.function(_get_pack_total, type="float", string='Packing Cost', store=True),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'quote_validity': fields.integer('Quote Validity', help="Validity of Quote in days."),
        'subject': fields.text('Subject'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice ID'),
        'dealers_disc': fields.function(_get_difference, type="float", string='Dealers Discount', store=True),
        'delivery_term': fields.integer('Delivery Term', help='Delivery Term in Weeks')
    }
    
    def manual_invoice(self, cr, uid, ids, context=None):
        """ create invoices for the given sales orders (ids), and open the form
            view of one of the newly created invoices
        """
        mod_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")

        # create invoices through the sales orders' workflow
        inv_ids0 = set(inv.id for sale in self.browse(cr, uid, ids, context) for inv in sale.invoice_ids)
        for id in ids:
            wf_service.trg_validate(uid, 'sale.order', id, 'manual_invoice', cr)
        inv_ids1 = set(inv.id for sale in self.browse(cr, uid, ids, context) for inv in sale.invoice_ids)
        # determine newly created invoices
        new_inv_ids = list(inv_ids1 - inv_ids0)
        self.write(cr, uid, ids[0], {'invoice_id': new_inv_ids[0]}, context=context)
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
        res_id = res and res[1] or False,

        return {
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': new_inv_ids and new_inv_ids[0] or False,
        }
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        stock_picking_obj = self.pool.get('stock.picking')
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        delivery_id = stock_picking_obj.search(cr, uid, [('sale_id', '=', order.id)], context=context)
        if delivery_id:
            delivery = stock_picking_obj.browse(cr, uid, delivery_id[0], context=context)
            delivery_date = delivery.date_done
            delivery_name = delivery.name
            res.update(
                {
                    'delivery_order_id': delivery_id[0],
                    'delivery_address_id': order.partner_shipping_id.id,
                    'date': order.date_order,
                    'carrier_id': order.carrier_id and order.carrier_id.id,
                    'delivery_name': delivery_name or None,
                    'delivery_date': delivery_date or False,
                    'sale_id': order.id
                }
            )
        return res
    
class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'
    
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        packing_cost_allowed = False
        res = super(sale_order_line, self)._amount_line(cr, uid, ids, field_name, arg, context=context)
        for id in ids:
            packing_cost_allowed = self.browse(cr, uid, id, context=context).order_id.company_id.packing_cost
        if packing_cost_allowed:
            for sale_order_line_id in res:
                qty = self.browse(cr, uid, sale_order_line_id, context=context).product_uom_qty
                packing_amount = self.browse(cr, uid, sale_order_line_id, context=context).packing_amount
                res[sale_order_line_id] += qty * packing_amount
        return res
    
    _columns = {
        'lst_price': fields.float('Dealers Price', help='Dealers Price'),
        'packing_amount': fields.float('Packing Cost'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account')),
    }
    
    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=0,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        context = context or {}
        lang = lang or context.get('lang', False)
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        if product:
            packing_cost_allowed = product_obj.browse(cr, uid, product, context=context).company_id.packing_cost
            dealers_discount_allowed = product_obj.browse(cr, uid, product, context=context).company_id.dealers_discount
            # Dealer's Discount Feature
            if dealers_discount_allowed:
                if partner_id:
                    partner_rec = partner_obj.browse(cr, uid, partner_id, context=context)
                    if partner_rec.dealer_id:
                        res['value']['lst_price'] = res['value']['price_unit']
                        res['value']['price_unit'] = 0.0
                    else:
                        res['value']['price_unit'] = res['value']['price_unit']
                        
            # Packing Feature
            if packing_cost_allowed:
                product_rec = product_obj.browse(cr, uid, product, context=context)
                if product_rec.packing_cost_type == 'fixed':
                    res['value']['packing_amount'] = float(product_rec.packing_fixed)
                else:
                    res['value']['packing_amount'] = float( ( res['value']['price_unit'] or res['value']['lst_price'] ) * product_rec.packing_percent / 100)
        return res
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line
        """
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)
        
        # Dealer's Discount Feature
        dealers_discount_allowed = self.browse(cr, uid, line.id, context=context).order_id.company_id.dealers_discount
        if dealers_discount_allowed:
            res['lst_price'] = line.lst_price
        
        # Packing Feature
        packing_cost_allowed = self.browse(cr, uid, line.id, context=context).order_id.company_id.packing_cost
        if packing_cost_allowed:
            res['packing_amount'] = line.packing_amount
            
        return res
    
class sale_order_line_make_invoice(osv.osv_memory):
    
    _inherit = "sale.order.line.make.invoice"
    _description = "Sale OrderLine Make_invoice"
    
    def make_invoices(self, cr, uid, ids, context=None):
        """
             To make invoices.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param ids: the ID or list of IDs
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        if context is None: context = {}
        res = False
        invoices = {}

    # TODO: merge with sale.py/make_invoice
        def make_invoice(order, lines):
            """
                 To make invoices.

                 @param order:
                 @param lines:

                 @return:

            """
            stock_picking_obj = self.pool.get('stock.picking')
            delivery_date = False
            delivery_name = ''
            a = order.partner_id.property_account_receivable.id
            if order.partner_id and order.partner_id.property_payment_term.id:
                pay_term = order.partner_id.property_payment_term.id
            else:
                pay_term = False
            delivery_id = stock_picking_obj.search(cr, uid, [('sale_id', '=', order.id)])
            for id in delivery_id:
                delivery_date = stock_picking_obj.browse(cr, uid, id, context=context).date_done
                delivery_name = stock_picking_obj.browse(cr, uid, id, context=context).name
            inv = {
                'name': order.name,
                'origin': order.name,
                'type': 'out_invoice',
                'reference': "P%dSO%d" % (order.partner_id.id, order.id),
                'account_id': a,
                'partner_id': order.partner_invoice_id.id,
                'invoice_line': [(6, 0, lines)],
                'currency_id' : order.pricelist_id.currency_id.id,
                'comment': order.note,
                'payment_term': pay_term,
                'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id,
                'user_id': order.user_id and order.user_id.id or False,
                'company_id': order.company_id and order.company_id.id or False,
                'date_invoice': fields.date.today(),
                'delivery_address_id': order.partner_shipping_id.id,
                'date': order.date_order,
                'carrier_id': order.carrier_id and order.carrier_id.id,
                'delivery_name': delivery_name,
                'delivery_date': delivery_date,
                'sale_id': order.id
            }
            inv_id = self.pool.get('account.invoice').create(cr, uid, inv)
            return inv_id

        sales_order_line_obj = self.pool.get('sale.order.line')
        sales_order_obj = self.pool.get('sale.order')
        wf_service = netsvc.LocalService('workflow')
        for line in sales_order_line_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if (not line.invoiced) and (line.state not in ('draft', 'cancel')):
                if not line.order_id.id in invoices:
                    invoices[line.order_id.id] = []
                line_id = sales_order_line_obj.invoice_line_create(cr, uid,
                        [line.id])
                for lid in line_id:
                    invoices[line.order_id.id].append((line, lid))
        for result in invoices.values():
            order = result[0][0].order_id
            il = map(lambda x: x[1], result)
            res = make_invoice(order, il)
            cr.execute('INSERT INTO sale_order_invoice_rel \
                    (order_id,invoice_id) values (%s,%s)', (order.id, res))

            flag = True
            data_sale = sales_order_obj.browse(cr, uid, line.order_id.id, context=context)
            for line in data_sale.order_line:
                if not line.invoiced:
                    flag = False
                    break
            if flag:
                wf_service.trg_validate(uid, 'sale.order', line.order_id.id, 'manual_invoice', cr)
                sales_order_obj.write(cr, uid, [line.order_id.id], {'state': 'progress'})

        if not invoices:
            raise osv.except_osv(_('Warning!'), _('Invoice cannot be created for this Sales Order Line due to one of the following reasons:\n1.The state of this sales order line is either "draft" or "cancel"!\n2.The Sales Order Line is Invoiced!'))
        if context.get('open_invoices', False):
            return self.open_invoices(cr, uid, ids, res, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
class stock_picking(osv.osv):
    
    _inherit = "stock.picking"
    
    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        res = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        freight_allowed = self.browse(cr, uid, picking.id, context=context).company_id.freight
        if picking.sale_id:
            res.update(
                {
                    'delivery_order_id': picking.id,
                    'delivery_address_id': picking.partner_id.id,
                    'date': picking.sale_id.date_order,
                    'carrier_id': picking.carrier_id and picking.carrier_id.id,
                    'delivery_name': picking.name,
                    'delivery_date': picking.date_done,
                    'sale_id': picking.sale_id.id
                }
            )
        if picking.purchase_id and freight_allowed:
            res.update(
                {
                    'freight_charge': picking.purchase_id.inward_freight,
                }
            )
        return res
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
            group=False, type='out_invoice', context=None):
        sale_order_obj = self.pool.get('sale.order')
        
        for id in ids:
            sale_id = self.browse(cr, uid, id, context=context).sale_id.id
        
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id=journal_id,
            group=group, type=type, context=context)
        
        for key in res:
            invoice_id = res[key]
        sale_order_obj.write(cr, uid, sale_id, {'invoice_id': invoice_id}, context=context)
        return res
        
    
    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=None):
        """ Builds the dict containing the values for the invoice line
            @param group: True or False
            @param picking: picking object
            @param: move_line: move_line object
            @param: invoice_id: ID of the related invoice
            @param: invoice_vals: dict used to created the invoice
            @return: dict that will be used to create the invoice line
        """
        res = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id,
        invoice_vals, context=context)
        
        dealers_discount_allowed = self.browse(cr, uid, picking.id, context=context).company_id.dealers_discount
        packing_cost_allowed = self.browse(cr, uid, picking.id, context=context).company_id.packing_cost
        
        # Dealer's Discount Feature
        if dealers_discount_allowed:
            res['lst_price'] = move_line.sale_line_id.lst_price or 0.0
        
        # Packing Feature
        if packing_cost_allowed:
            res['packing_amount'] = move_line.sale_line_id.packing_amount or 0.0
        return res
    
class account_invoice(osv.osv):
    
    _inherit = 'account.invoice'
    
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = super(account_invoice, self)._amount_all(cr, uid, ids, name, args, context=context)
        for invoice_id in res:
            freight_allowed = self.browse(cr, uid, invoice_id, context=context).company_id.freight
            if freight_allowed:
                freight_charge = self.browse(cr, uid, invoice_id, context=context).freight_charge
                res[invoice_id]['amount_total'] += freight_charge
        return res
    
    def _get_invoice_tax(self, cr, uid, ids, context=None):
        res = super(account_invoice, self.pool.get('account.invoice'))._get_invoice_tax(cr, uid, ids, context=context)
        return res
    
    def _get_invoice_line(self, cr, uid, ids, context=None):
        res = super(account_invoice, self.pool.get('account.invoice'))._get_invoice_line(cr, uid, ids, context=context)
        return res
    
    def _get_pack_total(self, cursor, user, ids, name, arg, context=None):
        res = {}
        tot_diff = 0.0
        for invoice in self.browse(cursor, user, ids, context=context):
            tot_diff = 0.0
            for line in invoice.invoice_line:
                tot_diff += line.packing_amount  # Need to check if packing cost apply by qty sold? 
            res[invoice.id] = tot_diff
        return res
    
    def _get_difference(self, cursor, user, ids, name, arg, context=None):
        res = {}
        tot_diff = 0.0
        for invoice in self.browse(cursor, user, ids):
            tot_diff = 0.0
            for line in invoice.invoice_line:
                if line.lst_price:
                    tot_diff += (line.price_unit - line.lst_price) * line.quantity
            res[invoice.id] = tot_diff
        return res
    
    def _get_qty_total(self, cr, uid, ids):
        res = {}
        qty = 0.0
        for invoice in self.browse(cr, uid, ids):
            for line in invoice.invoice_line:
                qty += line.quantity
            res[invoice.id] = qty
        return res
    
    def amount_to_text(self, amount, currency):
        amount_in_word = amount_to_text(amount)
        if currency == 'INR':
            amount_in_word = amount_in_word.replace("euro", "Rupees").replace("Cents", "Paise").replace("Cent", "Paise")
        return amount_in_word
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'delivery_order_id':False,
            'delivery_address_id': False,
            'carrier_id': False,
            'date': False,
            'delivery_name': False,
            'delivery_date': False,
            'sale_id': False,
            'dispatch_doc_no': False,
            'dispatch_doc_date': False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def _check_freight_allowed(self, cr, uid, ids, context=None):
        res_company_obj = self.pool.get('res.company')
        freight_allowed = res_company_obj.browse(cr, uid, uid, context=context).freight
        return freight_allowed
    
    _columns = {
        'delivery_order_id': fields.many2one('stock.picking', 'Delivery Order', readonly="True"),
        'delivery_address_id': fields.many2one('res.partner', 'Delivery Address'),
        'date': fields.date('Sales Date'),
        'carrier_id': fields.many2one('delivery.carrier', 'Carrier'),
        'delivery_name': fields.char('Delivery Name'),
        'delivery_date': fields.datetime('Delivery Date'),
        'sale_id': fields.many2one('sale.order', 'Sale Order ID', readonly="True"),
        'dispatch_doc_no': fields.char('Dispatch Document No.', size=16),
        'dispatch_doc_date': fields.date('Dispatch Document Date'),
        'consignee_account': fields.char('Consignee Account', size=32, help="Account Name, applies when there is customer for consignee."),
        'dealers_disc': fields.function(_get_difference, type="float", string='Dealers Discount', store=True),
        'packing_total': fields.function(_get_pack_total, type="float", string='Packing Cost', store=True),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
        store={
            'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
            'account.invoice.tax': (_get_invoice_tax, None, 20),
            'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
        },
        multi='all'),
                
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
                
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'freight_charge': fields.float('Inward Freight'),
        'freight_allowed': fields.boolean('Freight Allowed'),
    }
    
    _defaults = {
         'freight_allowed': _check_freight_allowed,
     }
    
#    def button_reset_taxes(self, cr, uid, ids, context=None):
#        if context is None:
#            context = {}
#        ctx = context.copy()
#        ait_obj = self.pool.get('account.invoice.tax')
#        for id in ids:
#            cr.execute("DELETE FROM account_invoice_tax WHERE invoice_id=%s AND manual is False", (id,))
#            partner = self.browse(cr, uid, id, context=ctx).partner_id
#            if partner.lang:
#                ctx.update({'lang': partner.lang})
#            for taxe in ait_obj.compute(cr, uid, id, context=ctx).values():
#                ait_obj.create(cr, uid, taxe)
#        # Update the stored value (fields.function), so we write to trigger recompute
#        self.pool.get('account.invoice').write(cr, uid, ids, {'invoice_line':[]}, context=ctx)
#        return True
#
#    def button_compute(self, cr, uid, ids, context=None, set_total=False):
#        self.button_reset_taxes(cr, uid, ids, context)
#        for inv in self.browse(cr, uid, ids, context=context):
#            if set_total:
#                self.pool.get('account.invoice').write(cr, uid, [inv.id], {'check_total': inv.amount_total})
#        return True
    
class account_invoice_line(osv.osv):
    
    _inherit = 'account.invoice.line'

    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = super(account_invoice_line, self)._amount_line(cr, uid, ids, prop, unknow_none, unknow_dict)
        packing_cost_allowed = False
        for id in ids:
            if self.browse(cr, uid, id).invoice_id:
                packing_cost_allowed = self.browse(cr, uid, id).invoice_id.company_id.packing_cost
        if packing_cost_allowed:
            for account_invoice_line_id in res:
                qty = self.browse(cr, uid, account_invoice_line_id).quantity
                packing_amount = self.browse(cr, uid, account_invoice_line_id).packing_amount
                res[account_invoice_line_id] += qty * packing_amount
        return res
    
    _columns = {
        'lst_price': fields.float('Dealers Price', help='Dealers Price'),
        'packing_amount': fields.float('Packing Cost'),
        'price_subtotal': fields.function(_amount_line, string='Amount', type="float", digits_compute=dp.get_precision('Account'), store=True),
    }
    
    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        res = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty=qty, name=name, type=type, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit, currency_id=currency_id, context=context, company_id=company_id)
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')

        if product:
            dealers_discount_allowed = product_obj.browse(cr, uid, product, context=context).company_id.dealers_discount
            packing_cost_allowed = product_obj.browse(cr, uid, product, context=context).company_id.packing_cost
            
            # Dealer's Discount Feature
            if dealers_discount_allowed:
                partner_rec = partner_obj.browse(cr, uid, partner_id, context=context)
                if not partner_rec.dealer_id:
                    res['value']['price_unit'] = res['value']['price_unit']
                else:
                    res['value']['lst_price'] = res['value']['price_unit']
                    res['value']['price_unit'] = 0.0
                
            # Packing Feature
            if packing_cost_allowed:    
                product_rec = product_obj.browse(cr, uid, product, context=context)
                if product_rec.packing_cost_type == 'fixed':
                    res['value']['packing_amount'] = float(product_rec.packing_fixed)
                else:
                    res['value']['packing_amount'] = float( ( res['value']['price_unit'] or res['value']['lst_price'] ) * product_rec.packing_percent / 100)
                    
        return res
    
class account_invoice_tax(osv.osv):
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        tax_grouped = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        cur = inv.currency_id
        company_currency = inv.company_id.currency_id.id
        packing_cost_allowed = inv.company_id.packing_cost
        for line in inv.invoice_line:
            if packing_cost_allowed:
                price_unit = ((line.price_unit + line.packing_amount)* (1-(line.discount or 0.0)/100.0))
            else:
                # Packing Cost Feature
                price_unit = (line.price_unit* (1-(line.discount or 0.0)/100.0))
            for tax in tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price_unit, line.quantity, line.product_id, inv.partner_id)['taxes']:
                tax_id = tax['id']
                val={}
                val['invoice_id'] = inv.id
                val['name'] = tax['name']
                val['amount'] = tax['amount']
                val['manual'] = False
                val['sequence'] = tax['sequence']
                val['base'] = cur_obj.round(cr, uid, cur, tax['price_unit'] * line['quantity'])
                val['tax_categ'] = tax_obj.browse(cr, uid, tax_id, context=context).tax_categ
                
                if inv.type in ('out_invoice','in_invoice'):
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

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
#    def amount_to_text(self, amount):
#        amount_in_word = amount_to_text(amount)
#        amount_in_word = amount_in_word.replace("euro", "Rupees").replace("Cents", "Paise").replace("Cent", "Paise")
#        return amount_in_word
    
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = super(purchase_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
        for purchase_id in res:
            freight_allowed = self.browse(cr, uid, purchase_id, context=context).company_id.freight
            if freight_allowed:
                inward_freight = self.browse(cr, uid, purchase_id, context=context).inward_freight
                res[purchase_id]['amount_total'] += inward_freight
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        res = super(purchase_order, self.pool.get('purchase.order'))._get_order(cr, uid, ids, context=context)
        return res
    
    def _check_freight_allowed(self, cr, uid, ids, context=None):
        res_company = self.pool.get('res.company')
        freight_allowed = res_company.browse(cr, uid, uid, context=context).freight
        return freight_allowed
    
    _columns = {
        'inward_freight': fields.float('Inward Freight'),
        'freight_allowed': fields.boolean('Freight Allowed'),
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
        store={
            'purchase.order.line': (_get_order, None, 10),
        }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
        store={
            'purchase.order.line': (_get_order, None, 10),
        }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
        store={
            'purchase.order.line': (_get_order, None, 10),
            'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['inward_freight'], 10),
        }, multi="sums", help="The total amount"),
    }
    
    _defaults = {
         'freight_allowed': _check_freight_allowed,
     }
    
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        res = super(purchase_order, self).action_invoice_create(cr, uid, ids, context=context)
        account_invoice_obj = self.pool.get('account.invoice')
        freight_allowed = False
        for id in ids:
            freight_allowed = self.browse(cr, uid, id, context=context).company_id.freight
            inward_freight = self.browse(cr, uid, id, context=context).inward_freight
        if freight_allowed:
            account_invoice_obj.write(cr, uid, res, {'freight_charge': inward_freight}, context=context)
            account_invoice_obj.button_compute(cr, uid, [res], context=context, set_total=True)
        return res
    
    def _get_qty_total(self, cr, uid, ids):
        res = {}
        qty = 0.0
        for order in self.browse(cr, uid, ids):
            for line in order.order_line:
                qty += line.product_qty
            res[order.id] = qty
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
