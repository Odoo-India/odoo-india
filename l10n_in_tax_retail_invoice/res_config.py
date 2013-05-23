# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2013 OpenERP S.A. (<http://openerp.com>).
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

class india_account_config_settings(osv.osv_memory):
    _name = 'india.account.config.settings'
    _inherit = 'res.config.settings'
    
    _columns = {
            'module_l10n_in_excise_customer_invoice': fields.boolean('Allow excise feature', help="Allows you to use excise feature. This installs module l10n_in_excise_customer_invoice."),
            'module_l10n_in_packing': fields.boolean('Allow packing cost feature', help="Allows you to use packing cost feature. This installs module l10n_in_packing."),
            'module_l10n_in_dealers_discount': fields.boolean('Allow dealers discount feature', help="Allows you to use dealers discount feature. This installs module l10n_in_dealers_discount."),
            'default_freight': fields.boolean('Allow freight feature', default_model='res.company', help="Allows you to use freight feature."),
            'module_l10n_in_delivery_challan': fields.boolean('Allow delivery challan feature', help="Allows you to use delivery challan feature. This installs module l10n_in_delivery_challan."),
            'module_l10n_in_form_402': fields.boolean('Allow form 402 feature', help="Allows you to use form 402 feature. This installs module l10n_in_form_402."),
            'module_l10n_in_account_check_writing_idbi': fields.boolean('Allow check writing feature in IDBI bank format', help="Allows you to use check writing feature in IDBI bank format. This installs module l10n_in_account_check_writing_idbi."),
            'module_l10n_in_tax_register': fields.boolean('Allow tax register feature in Excel format', help="Allows you to use tax register feature in Excel format. This installs module l10n_in_tax_register."),
            'module_sale_after_service': fields.boolean('Allow sale after service feature', help="Allows you to use sale after service feature. This installs module sale_after_service."),
            'module_l10n_in_cform': fields.boolean('Allow C-Form feature', help="Allows you to use C-Form feature. This installs module l10n_in_cform."),
        }
    
    def execute(self, cr, uid, ids, context=None):
        ir_module_obj = self.pool.get('ir.module.module')
        res_company_obj = self.pool.get('res.company')
        res_user_obj = self.pool.get('res.users')
        product_product_obj = self.pool.get('product.product')
        res_partner_obj = self.pool.get('res.partner')
        
        res = super(india_account_config_settings, self).execute(cr, uid, ids, context=context)
        
        packing_cost_module_id = ir_module_obj.search(cr, uid, [('name', '=', 'l10n_in_packing')], context=context)[0]
        
        packing_cost_module_state = ir_module_obj.browse(cr, uid, packing_cost_module_id, context=context).state
        company_id = res_user_obj.browse(cr, uid, uid, context=context).company_id.id
        
        if packing_cost_module_state == 'installed':
            res_company_obj.write(cr, uid, company_id, {'packing_cost': True}, context=context) 
        else:
            res_company_obj.write(cr, uid, company_id, {'packing_cost': False}, context=context)
            product_ids = product_product_obj.search(cr, uid, [], context=context)
            product_product_obj.write(cr, uid, product_ids, {}, context=context)
            
        dealers_discount_module_id = ir_module_obj.search(cr, uid, [('name', '=', 'l10n_in_dealers_discount')], context=context)[0]
        dealers_discount_module_state = ir_module_obj.browse(cr, uid, dealers_discount_module_id, context=context).state
        if dealers_discount_module_state == 'installed':
            res_company_obj.write(cr, uid, company_id, {'dealers_discount': True}, context=context) 
        else:
            res_company_obj.write(cr, uid, company_id, {'dealers_discount': False}, context=context)
            partner_ids = res_partner_obj.search(cr, uid, [], context=context)
            res_partner_obj.write(cr, uid, partner_ids, {}, context=context)   
        return res
    
    def set_freight(self, cr, uid, ids, context=None):
        res_company_obj = self.pool.get('res.company')
        res_user_obj = self.pool.get('res.users')
        freight = self.browse(cr, uid, ids[0], context=context).default_freight
        company_id = res_user_obj.browse(cr, uid, uid, context=context).company_id.id
        res_company_obj.write(cr, uid, company_id, {'freight': freight}, context=context)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: