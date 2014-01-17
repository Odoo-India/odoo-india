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

from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv,fields
from openerp import netsvc
from openerp import pooler
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns= {
        'origin': fields.char('Source Document', size=64,
            help="Reference of the document that created this Procurement.\n"
            "This is automatically completed by OpenERP." ,readonly=True),
    }

    def make_mo(self, cr, uid, ids, context=None):
        """
        -Process
            - Overwrite this function only to "draft" production order instead of "confirm" stage
        -Result
            - AS it is
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        production_obj = self.pool.get('mrp.production')
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            newdate = datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.product_id.produce_delay or 0.0)
            newdate = newdate - relativedelta(days=company.manufacturing_lead)
            produce_id = production_obj.create(cr, uid, {
                'origin': procurement.origin,
                'product_id': procurement.product_id.id,
                'product_qty': procurement.product_qty,
                'product_uom': procurement.product_uom.id,
                'product_uos_qty': procurement.product_uos and procurement.product_uos_qty or False,
                'product_uos': procurement.product_uos and procurement.product_uos.id or False,
                'location_src_id': procurement.location_id.id,
                'location_dest_id': procurement.location_id.id,
                'bom_id': procurement.bom_id and procurement.bom_id.id or False,
                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                'move_prod_id': res_id,
                'company_id': procurement.company_id.id,
            })
            
            res[procurement.id] = produce_id
            self.write(cr, uid, [procurement.id], {'state': 'running', 'production_id': produce_id})   
            bom_result = production_obj.action_compute(cr, uid,
                    [produce_id], properties=[x.id for x in procurement.property_ids])
            #no need to confirm production order based on procurmenet
            #wf_service.trg_validate(uid, 'mrp.production', produce_id, 'button_confirm', cr)
            if res_id:
                move_obj.write(cr, uid, [res_id],
                        {'location_id': procurement.location_id.id})
        self.production_order_create_note(cr, uid, ids, context=context)
        return res

    def _get_warehouse(self, procurement, user_company):
        """
            Return the warehouse containing the procurment stock location (or one of it ancestors)
            If none match, returns then first warehouse of the company
        """
        # TODO refactor the domain once we implement the "parent_of" domain operator
        # NOTE This method has been copied in the `purchase_requisition` module to ensure
        #      retro-compatibility. This code duplication will be deleted in next stable version.
        #      Do not forget to update both version in case of modification.
        company_id = (procurement.company_id or user_company).id
        domains = [
            [
                '&', ('company_id', '=', company_id),
                '|', '&', ('lot_stock_id.parent_left', '<', procurement.location_id.parent_left),
                          ('lot_stock_id.parent_right', '>', procurement.location_id.parent_right),
                     ('lot_stock_id', '=', procurement.location_id.id)
            ],
            [('company_id', '=', company_id)]
        ]

        cr, uid = procurement._cr, procurement._uid
        context = procurement._context
        Warehouse = self.pool['stock.warehouse']
        for domain in domains:
            ids = Warehouse.search(cr, uid, domain, context=context)
            if ids:
                return ids[0]
        return False

    def make_po(self, cr, uid, ids, context=None):
        """ Make purchase order from procurement
        @return: New created Purchase Orders procurement wise
        """
        res = {}
        if context is None:
            context = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id
        partner_obj = self.pool.get('res.partner')
        uom_obj = self.pool.get('product.uom')
        pricelist_obj = self.pool.get('product.pricelist')
        prod_obj = self.pool.get('product.product')
        acc_pos_obj = self.pool.get('account.fiscal.position')
        seq_obj = self.pool.get('ir.sequence')
        for procurement in self.browse(cr, uid, ids, context=context):
            res_id = procurement.move_id.id
            partner = procurement.product_id.seller_id # Taken Main Supplier of Product of Procurement.
            seller_qty = procurement.product_id.seller_qty
            partner_id = partner.id
            address_id = partner_obj.address_get(cr, uid, [partner_id], ['delivery'])['delivery']
            pricelist_id = partner.property_product_pricelist_purchase.id
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

                #ADD PUCHASE QTY
                'line_qty': procurement.product_id.p_coefficient * qty,
                'line_uom_id': procurement.product_id.p_uom_id.id,

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
                'warehouse_id': self._get_warehouse(procurement, company),
                'pricelist_id': pricelist_id,
                'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'company_id': procurement.company_id.id,
                'fiscal_position': partner.property_account_position and partner.property_account_position.id or False,
                'payment_term_id': partner.property_supplier_payment_term.id or False,
            }
            res[procurement.id] = self.create_procurement_purchase_order(cr, uid, procurement, po_vals, line_vals, context=new_context)
            self.write(cr, uid, [procurement.id], {'state': 'running', 'purchase_id': res[procurement.id]})
        self.message_post(cr, uid, ids, body=_("Draft Purchase Order created"), context=context)
        return res

    #its should apply for direclty purchase order will be generated in QC location(Stock Input Location)
    #So another idea we have done, like 
    #PO generate in Store Location, Incoming Shipment will be geneate first in QC location then Go to Store,
    #otherwise its directly goes to PO destination location.
#    def _prepare_orderpoint_procurement(self, cr, uid, orderpoint, product_qty, context=None):
#        """
#        -Process
#            -call super method to generate procurement dictonary
#            -Overwrite procurement location == Warehouse Location Input Id(Quality Control)
#            Why need ?
#                -Standard Process,
#                    Procurement -> Store,
#                -Now,
#                    Procurement -> Quality Control(input id),
#        """
#        res = super(procurement_order,self)._prepare_orderpoint_procurement(cr, uid, orderpoint, product_qty, context=context)
#        if orderpoint and orderpoint.warehouse_id:
#            res.update({'location_id': orderpoint.warehouse_id.lot_input_id.id})
#        return res

    def _procure_orderpoint_confirm(self, cr, uid, automatic=False,\
            use_new_cursor=False, context=None, user_id=False):
        '''
        Create procurement based on Orderpoint
        use_new_cursor: False or the dbname

        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param user_id: The current user ID for security checks
        @param context: A standard dictionary for contextual values
        @param param: False or the dbname
        @return:  Dictionary of values

        @Overwrite Process
        -Process
            -IDS TO GET Filter values
                -Find procurement active_id,
                    -Find product ids of those all procurements,
                        -Find to all minimum order rules bases on product_ids.
                            -Run those order points.
        '''

        def _get_product_ids(ids_to):
            p_ids = []
            procurement_obj = self.pool.get('procurement.order')
            for proc in procurement_obj.browse(cr, uid, ids_to):
                p_ids.append(proc.product_id.id)
            return filter(None,set(p_ids))

        if context is None:
            context = {}
        if use_new_cursor:
            cr = pooler.get_db(use_new_cursor).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')

        procurement_obj = self.pool.get('procurement.order')
        wf_service = netsvc.LocalService("workflow")
        offset = 0
        ids = [1]
        if automatic:
            self.create_automatic_op(cr, uid, context=context)
        while ids:

            #Process Overwrite
            if context and context.get('active_model') == 'procurement.order' and context.get('active_ids'):
                product_ids = _get_product_ids(context['active_ids'])
                ids = orderpoint_obj.search(cr, uid, [('active','=',True),('product_id','in',product_ids)], offset=offset, limit=100)
            else:
                ids = orderpoint_obj.search(cr, uid, [], offset=offset, limit=100)

            for op in orderpoint_obj.browse(cr, uid, ids, context=context):
                prods = self._product_virtual_get(cr, uid, op)
                if prods is None:
                    continue
                if prods < op.product_min_qty:
                    qty = max(op.product_min_qty, op.product_max_qty)-prods

                    reste = qty % op.qty_multiple
                    if reste > 0:
                        qty += op.qty_multiple - reste

                    if qty <= 0:
                        continue
                    if op.product_id.type not in ('consu'):
                        if op.procurement_draft_ids:
                        # Check draft procurement related to this order point
                            pro_ids = [x.id for x in op.procurement_draft_ids]
                            procure_datas = procurement_obj.read(
                                cr, uid, pro_ids, ['id', 'product_qty'], context=context)
                            to_generate = qty
                            for proc_data in procure_datas:
                                if to_generate >= proc_data['product_qty']:
                                    wf_service.trg_validate(uid, 'procurement.order', proc_data['id'], 'button_confirm', cr)
                                    procurement_obj.write(cr, uid, [proc_data['id']],  {'origin': op.name}, context=context)
                                    to_generate -= proc_data['product_qty']
                                if not to_generate:
                                    break
                            qty = to_generate
                    if qty:
                        proc_id = procurement_obj.create(cr, uid,
                                                         self._prepare_orderpoint_procurement(cr, uid, op, qty, context=context),
                                                         context=context)
                        wf_service.trg_validate(uid, 'procurement.order', proc_id,
                                'button_confirm', cr)
                        wf_service.trg_validate(uid, 'procurement.order', proc_id,
                                'button_check', cr)
                        orderpoint_obj.write(cr, uid, [op.id],
                                {'procurement_id': proc_id}, context=context)
            offset += len(ids)
            if use_new_cursor:
                cr.commit()
        if use_new_cursor:
            cr.commit()
            cr.close()
        return {}

procurement_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
