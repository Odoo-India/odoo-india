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
from osv import osv
from osv import fields
from tools.translate import _
import datetime

class split_company_data(osv.osv_memory):
    _name = 'account.split.company.data'
    _columns = {
         'company_id': fields.many2one('res.company', 'Company to Split', required=True),
         'period_id': fields.many2one('account.period', 'Period'),
         'first_company_name': fields.char('First Company Name', size=64, required=True),
         'second_company_name': fields.char('Second Company Name', size=64, required=True),
         'type': fields.selection( [('percent','Percentage'), ('period','Period')], 'Split Type', required=True, select=True),
         'first_comp_percent': fields.float('First Company Percentage'),
         'second_comp_percent': fields.float('Second Company Percentage'),
    }

    _defaults = {
        'type': 'period',
    }

    def onchange_percentage(self, cr, uid, ids, percent):
        result = {}
        result = {'value':{'second_comp_percent': (100.0 - percent)}}
        return result

    def create_account(self, cr, uid, old_company_id, new_company_id, name, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        company_obj = self.pool.get('res.company')
        account_obj = self.pool.get('account.account')
        partner_obj = self.pool.get('res.partner')

        main_company_data = company_obj.browse(cr, uid, old_company_id, context=context)
        root_account_id = account_obj.search(cr, uid, [('name','=',main_company_data.name),('company_id','=',old_company_id)], context=context)

        root_account_data = account_obj.browse(cr, uid, root_account_id[0], context=context)

        comp_main_account_id = account_obj.create(cr, uid, {
                                            'name':name,
                                            'user_type': root_account_data.user_type.id,
                                            'type': root_account_data.type,
                                            'code': root_account_data.code,
                                            'company_id': new_company_id
                                        })

        cr.execute("""SELECT id, parent_id, company_id FROM account_account WHERE company_id=%s AND parent_id IS NOT NULL order by parent_id """, (old_company_id,))
        account_ids = map(lambda x: x['id'], cr.dictfetchall())

        # create account of for the first company
        for account_id in account_ids:
            account_parent_id = False
            new_child_consol_ids = []
            data = account_obj.browse(cr, uid, account_id, context=context)
            account_id = account_obj.search(cr, uid, [('company_id','=', new_company_id),('name','=',data.name), ('code','=',data.code)])

            if account_id:
                continue

            if data.parent_id:
                account_parent_id = account_obj.search(cr, uid, [('company_id','=', new_company_id),('name','=',data.parent_id.name),('code','=',data.parent_id.code)])

            if data.child_consol_ids:
                for child_consol_data in data.child_consol_ids:
                    child_consol_id = account_obj.search(cr, uid, [('company_id','=', new_company_id),('name','=',child_consol_data.name), ('code','=',child_consol_data.code)])
                    if child_consol_id:
                        new_child_consol_ids.append(child_consol_id[0])

            if account_parent_id:
                account_parent_id = account_parent_id[0]
            else:
                account_parent_id = comp_main_account_id

            account_obj.create(cr, uid, {
                                        'name': data.name,
                                        'company_id':new_company_id,
                                        'code': data.code,
                                        'user_type': data.user_type.id,
                                        'type': data.type,
                                        'parent_id': account_parent_id,
                                        'reconcile': data.reconcile,
                                        'currency_mode':data.currency_mode,
                                        'currency_id':data.currency_id.id,
                                        'child_consol_ids':new_child_consol_ids,
                                        }
                                   )
        return True

    def create_account_journal(self, cr, uid, old_company_id, new_company_id, context=None):
        if context is None:
            context = {}

        journal_obj = self.pool.get('account.journal')
        sequence_obj = self.pool.get('ir.sequence')
        account_obj = self.pool.get('account.account')
        analytic_journal_obj = self.pool.get('account.analytic.journal')

        journal_ids = journal_obj.search(cr, uid, [('company_id','=',old_company_id)], context=context)

        for journal_id in journal_ids:

            new_seq_id = False
            new_default_credit_account_id = False
            new_default_debit_account_id = False
            new_analytic_journal_id = False

            journal_data = journal_obj.browse(cr, uid, journal_id, context=context)

            new_journal_id = journal_obj.search(cr, uid, [('company_id','=',new_company_id),('name','=',journal_data.name),('code','=',journal_data.code)], context=context)

            if not new_journal_id:

                if journal_data.default_credit_account_id:
                    account_data = account_obj.browse(cr, uid, journal_data.default_credit_account_id.id, context=context)
                    credit_account_id = account_obj.search(cr, uid, [('name','=',account_data.name),('code','=',account_data.code),('company_id','=',new_company_id)])
                    new_default_credit_account_id = credit_account_id[0]

                if journal_data.default_debit_account_id:
                    account_data = account_obj.browse(cr, uid, journal_data.default_debit_account_id.id, context=context)
                    debit_account_id = account_obj.search(cr, uid, [('name','=',account_data.name),('code','=',account_data.code),('company_id','=',new_company_id)])
                    new_default_debit_account_id = debit_account_id[0]

                if journal_data.analytic_journal_id:
                    analytic_journal_data = analytic_journal_obj.browse(cr, uid, journal_data.analytic_journal_id.id, context=context)
                    new_analytic_journal_id = analytic_journal_obj.search(cr, uid, [('name','=',analytic_journal_data.name),('code','=',analytic_journal_data.name),('company_id','=',new_company_id)])
                    if not new_analytic_journal_id:
                        new_analytic_journal_id = analytic_journal_obj.create(cr, uid, {
                                                                                        'name':analytic_journal_data.name,
                                                                                        'code':analytic_journal_data.code,
                                                                                        'company_id':new_company_id,
                                                                                        'type':analytic_journal_data.type
                                                                                        }, context=context)
                if journal_data.sequence_id.id:
                    seq_data = sequence_obj.browse(cr, uid, journal_data.sequence_id.id, context=context)

                    vals_seq = {
                        'name':seq_data.name,
                        'code':seq_data.code,
                        'padding':seq_data.padding,
                        'prefix':seq_data.prefix,
                        'company_id':new_company_id,
                        }

                    new_seq_id = sequence_obj.create(cr, uid, vals_seq, context=context)

                vals_journal = {
                        'name': journal_data.name,
                        'code': journal_data.code,
                        'sequence_id': new_seq_id,
                        'type': journal_data.type,
                        'company_id': new_company_id,
                        'view_id': journal_data.view_id.id,
                        'analytic_journal_id':new_analytic_journal_id,
                        'default_credit_account_id':new_default_credit_account_id,
                        'default_debit_account_id':new_default_debit_account_id,
                        }

                journal_obj.create(cr, uid, vals_journal, context=context)

        return True

    def create_account_period(self, cr, uid, old_company_id, new_company_id, name, context=None):
        if context is None:
            context = {}

        fiscal_obj = self.pool.get('account.fiscalyear')
        account_obj = self.pool.get('account.account')

        diff_days = 0.0

        old_fiscal_id = fiscal_obj.search(cr, uid, [('company_id', '=', old_company_id)], context=context)[0]
        old_fiscal_data = fiscal_obj.browse(cr, uid, old_fiscal_id, context=context)
        new_fiscal_id = fiscal_obj.search(cr, uid, [('date_start', '<=', old_fiscal_data.date_start), ('date_stop', '>=', old_fiscal_data.date_stop), ('company_id', '=', new_company_id)], context=context)

        if not new_fiscal_id:
            name = old_fiscal_data.date_start[:4] + '('+name+')'
            code = 'FY' + old_fiscal_data.date_start[:4]
            vals = {
                'name': name,
                'code': code,
                'date_start': old_fiscal_data.date_start,
                'date_stop': old_fiscal_data.date_stop,
                'company_id': new_company_id
            }

            # Creation of Period monthly or Quarterly
            new_fiscal_id = fiscal_obj.create(cr, uid, vals, context=context)
            period_data_start =  datetime.datetime.strptime(old_fiscal_data.period_ids[0].date_start, "%Y-%m-%d")
            period_data_stop =  datetime.datetime.strptime(old_fiscal_data.period_ids[0].date_stop, "%Y-%m-%d")
            diff_days = (period_data_stop - period_data_start).days
            if diff_days > 31:
                fiscal_obj.create_period3(cr, uid, [new_fiscal_id])
            else:
                fiscal_obj.create_period(cr, uid, [new_fiscal_id])

        return True

    def create_account_move_entry(self, cr, uid, old_company_id, new_company_id1, new_company_id2, period_id, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        obj_sequence = self.pool.get('ir.sequence')

        move_ids = move_obj.search(cr, uid, [('company_id','=',old_company_id)])

        for move_id in move_ids:
            move_data = move_obj.browse(cr, uid, move_id, context=context)
            new_period_id = False
            new_journal_id = False
            move_line_journal_id = False
            name = False
            # Find period for the new company
            period_data = period_obj.browse(cr, uid, period_id, context=context)

            if move_data.period_id.date_stop < period_data.date_start:
                new_period_id = period_obj.search(cr, uid, [('name','=',move_data.period_id.name),('company_id','=',new_company_id1)], context=context)
            else:
                new_period_id = period_obj.search(cr, uid, [('name','=',move_data.period_id.name),('company_id','=',new_company_id2)], context=context)


            # Find jorunal for new company
            journal_data = journal_obj.browse(cr, uid, move_data.journal_id.id, context=context)

            if move_data.period_id.date_stop < period_data.date_start:
                new_journal_id = journal_obj.search(cr, uid, [('name','=',journal_data.name),('code','=',journal_data.code),('company_id','=',new_company_id1)], context=context)
            else:
                new_journal_id = journal_obj.search(cr, uid, [('name','=',journal_data.name),('code','=',journal_data.code),('company_id','=',new_company_id2)], context=context)

            new_move_id = move_obj.create(cr, uid, {
                                                    'name': move_data.name,
                                                    'ref': move_data.ref,
                                                    'period_id': new_period_id[0],
                                                    'journal_id': new_journal_id[0],
                                                    'date': move_data.date,
                                                    'state': 'draft',
                                                    }, context=context)

            move_line_ids = move_line_obj.search(cr, uid, [('move_id','=',move_id)])
            reconcile_line_ids = []
            for move_line_id in move_line_ids:
                move_line_data = move_line_obj.browse(cr, uid, move_line_id, context=context)

                # Find Account for move line entry
                move_line_account_data = account_obj.browse(cr, uid, move_line_data.account_id.id, context=context)
                if move_data.period_id.date_stop < period_data.date_start:
                    move_line_account_id = account_obj.search(cr, uid, [('name','=',move_line_account_data.name),('code','=',move_line_account_data.code),('company_id','=',new_company_id1)])
                else:
                    move_line_account_id = account_obj.search(cr, uid, [('name','=',move_line_account_data.name),('code','=',move_line_account_data.code),('company_id','=',new_company_id2)])

                new_move_line_id = move_line_obj.create(cr, uid, {
                                                                  'name': move_line_data.name,
                                                                  'journal_id': new_journal_id[0],
                                                                  'period_id': new_period_id[0],
                                                                  'account_id': move_line_account_id[0],
                                                                  'debit': move_line_data.debit,
                                                                  'credit': move_line_data.credit,
                                                                  'partner_id': move_line_data.partner_id.id,
                                                                  'currency_id': move_line_data.currency_id.id,
                                                                  'amount_currency': move_line_data.amount_currency,
                                                                  'date': move_line_data.date,
                                                                  'date_maturity': move_line_data.date_maturity,
                                                                  'move_id': new_move_id,
                                                                  }, context=context)
            #Post entry
            move_obj.post(cr, uid, [new_move_id], context=context) # To post entry
        # TODO Reconcile entry

        return True

    def create_account_move_entry_percent(self, cr, uid, old_company_id, new_company_id, percent, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        journal_obj = self.pool.get('account.journal')
        period_obj = self.pool.get('account.period')
        obj_sequence = self.pool.get('ir.sequence')

        move_ids = move_obj.search(cr, uid, [('company_id','=',old_company_id)])

        for move_id in move_ids:
            move_data = move_obj.browse(cr, uid, move_id, context=context)
            new_period_id = False
            new_journal_id = False
            move_line_journal_id = False
            name = False
            # find period for the new company
            period_data = period_obj.browse(cr, uid, move_data.period_id.id, context=context)
            new_period_id = period_obj.search(cr, uid, [('name','=',period_data.name),('company_id','=',new_company_id)], context=context)

            # find jorunal for tne new company
            journal_data = journal_obj.browse(cr, uid, move_data.journal_id.id, context=context)
            new_journal_id = journal_obj.search(cr, uid, [('name','=',journal_data.name),('code','=',journal_data.code),('company_id','=',new_company_id)], context=context)

            new_move_id = move_obj.create(cr, uid, {
                                                    'name': '/',
                                                    'period_id': new_period_id[0],
                                                    'journal_id': new_journal_id[0],
                                                    'date': move_data.date,
                                                    'state': 'draft',
                                                    }, context=context)

            move_line_ids = move_line_obj.search(cr, uid, [('move_id','=',move_id)])
            reconcile_line_ids = []
            for move_line_id in move_line_ids:
                move_line_data = move_line_obj.browse(cr, uid, move_line_id, context=context)
                #Account for the move line
                move_line_account_data = account_obj.browse(cr, uid, move_line_data.account_id.id, context=context)
                move_line_account_id = account_obj.search(cr, uid, [('name','=',move_line_account_data.name),('code','=',move_line_account_data.code),('company_id','=',new_company_id)])
                new_move_line_id = move_line_obj.create(cr, uid, {
                                                                  'name': move_line_data.name,
                                                                  'journal_id': new_journal_id[0],
                                                                  'period_id': new_period_id[0],
                                                                  'account_id': move_line_account_id[0],
                                                                  'debit': (move_line_data.debit * percent / 100),
                                                                  'credit': (move_line_data.credit * percent / 100),
                                                                  'partner_id': move_line_data.partner_id.id,
                                                                  'currency_id': move_line_data.currency_id.id,
                                                                  'amount_currency': move_line_data.amount_currency,
                                                                  'date': move_line_data.date,
                                                                  'date_maturity': move_line_data.date_maturity,
                                                                  'move_id': new_move_id,
                                                                  }, context=context)
            #Post entry
            move_obj.post(cr, uid, [new_move_id], context=context) # To post entry
            # TODO Reconcile entry
        return True

    def assign_property_account(self, cr, uid, company_id, company_name, context=None):
        if context is None:
            context={}

        property_obj = self.pool.get('ir.property')
        partner_obj = self.pool.get('res.partner')
        account_obj = self.pool.get('account.account')

        partner_id = partner_obj.search(cr, uid,[('name','=',company_name)])
        partner_data = partner_obj.browse(cr, uid, partner_id, context=context)

        rec_pro_id = property_obj.search(cr,uid,[('name','=','property_account_receivable'),('company_id','=',company_id)])
        pay_pro_id = property_obj.search(cr,uid,[('name','=','property_account_payable'),('company_id','=',company_id)])

        old_rec_pro_id = property_obj.browse(cr, uid, rec_pro_id[0], context=context).value_reference.id
        old_pay_pro_id = property_obj.browse(cr, uid, pay_pro_id[0], context=context).value_reference.id

        account_rec = account_obj.browse(cr, uid, old_rec_pro_id, context=context)
        account_pay = account_obj.browse(cr, uid, old_pay_pro_id, context=context)

        return {
                'property_rec_name':account_rec.name,
                'property_rec_code':account_rec.code,
                'property_pay_name':account_pay.name,
                'property_pay_code':account_pay.code
                }

    def split_data(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        company_obj = self.pool.get('res.company')
        account_obj = self.pool.get('account.account')
        partner_obj = self.pool.get('res.partner')

        data = self.read(cr, uid, ids, [])[0]

        main_period = data['period_id']
        main_company_data = company_obj.browse(cr, uid, data['company_id'], context=context)
        root_account_id = account_obj.search(cr, uid, [('name','=',main_company_data.name)], context=context)
        root_account_data = account_obj.browse(cr, uid, root_account_id[0], context=context)

        # created first company partner
        first_part_id = partner_obj.create(cr, uid,{
                                                'name':data['first_company_name'],
                                                },context=context)
        # created second company partner
        second_part_id = partner_obj.create(cr, uid,{
                                            'name':data['second_company_name'],
                                           },context=context)
        # created first company
        first_company_id = company_obj.create(cr, uid, {
                                        'name':data['first_company_name'],
                                        'currency_id':main_company_data.currency_id.id,
                                        'partner_id': first_part_id,
                                        }, context=context)
        # created second company
        second_company_id = company_obj.create(cr, uid, {
                                        'name':data['second_company_name'],
                                        'currency_id':main_company_data.currency_id.id,
                                        'partner_id': second_part_id,
                                        }, context=context)

        # Created account for the first company from main company
        self.create_account(cr, uid, data['company_id'], first_company_id, data['first_company_name'], context=context)

        # Created period for the first company
        self.create_account_period(cr, uid, data['company_id'], first_company_id, data['first_company_name'], context=context)

        # Created account for the second company from main company
        self.create_account(cr, uid, data['company_id'], second_company_id, data['second_company_name'], context=context)

        # Created period for the second company
        self.create_account_period(cr, uid, data['company_id'], second_company_id, data['second_company_name'], context=context)

        #Created journal for the first company
        self.create_account_journal(cr, uid,  data['company_id'], first_company_id, context=context)

        #Created journal for the second company
        self.create_account_journal(cr, uid,  data['company_id'], second_company_id, context=context)

        # Assing property account to companies partner
        prorperty_account = self.assign_property_account(cr, uid, data['company_id'], main_company_data.name, context=context)
        first_comp_rec_acc = account_obj.search(cr, uid, [('company_id','=', first_company_id),('name','=',prorperty_account['property_rec_name']),('code','=',prorperty_account['property_rec_code'])])
        first_comp_pay_acc = account_obj.search(cr, uid, [('company_id','=', first_company_id),('name','=',prorperty_account['property_pay_name']),('code','=',prorperty_account['property_pay_code'])])

        second_comp_rec_acc = account_obj.search(cr, uid, [('company_id','=', second_company_id),('name','=',prorperty_account['property_rec_name']),('code','=',prorperty_account['property_rec_code'])])
        second_comp_pay_acc = account_obj.search(cr, uid, [('company_id','=', second_company_id),('name','=',prorperty_account['property_pay_name']),('code','=',prorperty_account['property_pay_code'])])

        partner_obj.write(cr, uid, [first_part_id], {'property_account_receivable':first_comp_rec_acc[0],'property_account_payable':first_comp_pay_acc[0]})
        partner_obj.write(cr, uid, [second_part_id], {'property_account_receivable':second_comp_rec_acc[0],'property_account_payable':second_comp_pay_acc[0]})

        # Created account move entry on the base of period
        if data['type'] == 'period':
            self.create_account_move_entry(cr, uid, data['company_id'], first_company_id, second_company_id, main_period, context=context)
        #Created account on the base of percentage
        else:
            if (data['first_comp_percent'] + data['second_comp_percent']) > 100:
                raise osv.except_osv(_('Error'), _('Please check your given percentage, both percentage total should not be more than 100 !'))
            # for first company percentage entry
            self.create_account_move_entry_percent(cr, uid, data['company_id'], first_company_id, data['first_comp_percent'], context=context)
            # for second company percentage entry
            self.create_account_move_entry_percent(cr, uid, data['company_id'], second_company_id, data['second_comp_percent'], context=context)

        return {}

split_company_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
