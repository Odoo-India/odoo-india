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
from operator import itemgetter
from osv import osv
from osv import fields

class setup_company_merge(osv.osv_memory):
    _name = 'setup.company.merge'
    _inherit = 'res.company'

    def _get_all(self, cr, uid, model, context=None):
        models = self.pool.get(model)
        all_model_ids = models.search(cr, uid, [])

        output = [(False, '')]
        output.extend(
            sorted([(o.id, o.name)
                    for o in models.browse(cr, uid, all_model_ids,
                                           context=context)],
                   key=itemgetter(1)))
        return output

    def _get_all_states(self, cr, uid, context=None):
        return self._get_all(
            cr, uid, 'res.country.state', context=context)
    def _get_all_countries(self, cr, uid, context=None):
        return self._get_all(cr, uid, 'res.country', context=context)

    _columns = {
        'company_id':fields.many2one('res.company', 'Company'),
        'name':fields.char('Company Name', size=64, required=True),
        'street':fields.char('Street', size=128),
        'street2':fields.char('Street 2', size=128),
        'zip':fields.char('Zip Code', size=24),
        'city':fields.char('City', size=128),
        'state_id':fields.selection(_get_all_states, 'Fed. State'),
        'country_id':fields.selection(_get_all_countries, 'Country'),
        'email':fields.char('E-mail', size=64),
        'phone':fields.char('Phone', size=64),
        'currency':fields.many2one('res.currency', 'Currency', required=True),
        'logo':fields.binary('Logo'),
        'account_no':fields.char('Bank Account No', size=64),
        'website': fields.char('Company Website', size=64, help="Example: http://openerp.com"),
    }

    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        company = self.pool.get('res.company')
        partner = self.pool.get('res.partner')
        mod_obj = self.pool.get('ir.model.data')

        payload = self.browse(cr, uid, ids[0], context=context)

        part_id=partner.create(cr, uid,{
            'name':payload.name,
            'website':payload.website,
            },context=context)

        new_comp = company.create(cr, uid, {
            'name':payload.name,
            'logo':payload.logo,
            'currency_id':payload.currency.id,
            'account_no':payload.account_no,
            'partner_id': part_id,
        }, context=context)

        address_data = {
            'name':payload.name,
            'street':payload.street,
            'street2':payload.street2,
            'zip':payload.zip,
            'city':payload.city,
            'email':payload.email,
            'phone':payload.phone,
            'country_id':int(payload.country_id),
            'state_id':int(payload.state_id),
            'partner_id':part_id,
        }

        add_id = self.pool.get('res.partner.address').create(cr, uid,
            address_data, context=context)

        context.update({'company_id': new_comp})

        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'),('name', '=', 'view_setup_company_merge2')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': 'Company Merge',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'company.account.merge',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
            }
setup_company_merge()


class company_account_merge(osv.osv_memory):
    _name = "company.account.merge"
    _columns = {
         'merge_companies_ids': fields.many2many('res.company', 'merge_company_rel', 'merge_id', 'company_id', 'Merge Company'),
    }

    def do_merge(self, cr, uid, ids, context=None):
        # merge account of company
        if context is None:
            context = {}

        company_obj = self.pool.get("res.company")
        account_obj = self.pool.get("account.account")
        account_type_obj = self.pool.get("account.account.type")

        data = self.read(cr, uid, ids, [])[0]

        new_company_name = company_obj.browse(cr, uid, context['company_id'], context=context).name
        account_type_id = account_type_obj.search(cr, uid,[('name','=','View')])

        account_code_id = account_obj.search(cr, uid, [('company_id','in',data['merge_companies_ids']),('parent_id','=',None)])
        account_code = account_obj.browse(cr, uid, account_code_id[0], context=context)
        print "==code========",account_code.code

        #Created main parent account
        main_account_id = account_obj.create(cr, uid, {
                                            'name':new_company_name,
                                            'user_type': account_type_id[0],
                                            'type': 'view',
                                            'code': account_code.code,
                                            'company_id': context['company_id']
                                        })

        # account list of views
        account_views_ids = account_obj.search(cr, uid, [('company_id','in',data['merge_companies_ids']),('parent_id','!=',None)], order="parent_id" )

        # create account of type view account
        for account_view_id in account_views_ids:
            consolidation_child = []
            view_data = account_obj.browse(cr, uid, account_view_id, context=context)
            view_account_id = account_obj.search(cr, uid, [('company_id','=', context['company_id']),('name','=',view_data.name)], order='parent_id')

            if view_account_id:
                continue

            view_account_parent_id = account_obj.search(cr, uid, [('company_id','=', context['company_id']),('name','=',view_data.parent_id.name),('code','=',view_data.parent_id.code)])

            if view_account_parent_id:
                account_parent_id = view_account_parent_id[0]
            else:
                account_parent_id = main_account_id

            consolidation_child_ids = account_obj.search(cr, uid, [('company_id','in',data['merge_companies_ids']),('type','!=','view'),('name','=',view_data.name),('code','=',view_data.code)])

            #creating view type account
            if view_data.type == 'view':
                account_obj.create(cr, uid, {
                                        'name': view_data.name,
                                        'company_id':context['company_id'],
                                        'code': view_data.code,
                                        'user_type': view_data.user_type.id,
                                        'type': 'view',
                                        'parent_id': account_parent_id
                                        }
                                   )
            #creating consolidate type account
            else:
                account_obj.create(cr, uid, {
                                    'name': view_data.name,
                                    'company_id':context['company_id'],
                                    'code': view_data.code,
                                    'user_type': view_data.user_type.id,
                                    'type': 'consolidation',
                                    'parent_id': account_parent_id,
                                    'child_consol_ids':[(6,0,consolidation_child_ids)]
                                    })
        return {}

company_account_merge()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
