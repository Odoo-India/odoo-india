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
from osv import fields, osv

class account_create(osv.TransientModel):
    _name = "account.create"
    _description = "Account Create"

    def create_account(self, cr, uid, ids, context=None):
        account_obj = self.pool.get('account.account')
        account_type_obj = self.pool.get('account.account.type')
        partner_obj =self.pool.get('res.partner')

        lia_ids = account_type_obj.search(cr, uid, [('code','=','receivable')], context=context)
        ass_ids = account_type_obj.search(cr, uid, [('code','=','payable')], context=context)

        if context is None:
            context = {}
        active_ids = context.get('active_ids', [])
        for partner in partner_obj.browse(cr, uid, active_ids, context=context):

            debit_id = account_obj.create(cr, uid, {
                'code': str(partner.name[0:3]) + 'dr',
                'name':'Debtors - (%s)' % (partner.name),
#                'parent_id':7,
                'type':'receivable',
                'reconcile':True,
                'user_type': lia_ids and lia_ids[0] or False,
                'company_id': 1,
            }, context=context)

            credit_id = account_obj.create(cr, uid, {
                'code': str(partner.name[0:3]) + 'cr',
                'name': 'Creditors - (%s)' % (partner.name),
#                'parent_id':16,
                'type': 'payable',
                'reconcile': True,
                'user_type': ass_ids and ass_ids[0] or False,
                'company_id': 1,
            }, context=context)

            partner_obj.write(cr, uid, partner.id, {
                'property_account_receivable': debit_id, 
                'property_account_payable': credit_id,
            }, context=context)

        return True

account_create()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
