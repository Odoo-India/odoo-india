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

from osv import fields, osv
import time

class account_invoice_cform(osv.osv_memory):
    
    _name = 'account.invoice.cform'
    
    _columns = {
            'account_ids': fields.many2many('account.account', 'account_cform_rel', 'cform_id', 'account_id', 'Accounts', help=" Keep empty to consider all accounts in report."),
            'partner_ids': fields.many2many('res.partner', 'partner_cform_rel', 'cform_id', 'partner_id', 'Partners', help="Keep empty to consider all partners in report."),
            'form_type': fields.selection([('c_form', 'C-Form'), ('h_form', 'H-Form'), ('i_form', 'I-Form'), ('e1_form', 'E1-Form')], 'Form Type', required=True, help="Select Form Type, for which you want to print the report."),
            'filter': fields.selection([('filter_no', 'No Filters'), ('filter_period', 'Periods')], "Filter by", required=True),
            'group_by': fields.selection([('by_partners', 'Partners'), ('by_accounts', 'Accounts')], "Group by", required=True, help="Accounts: Prints report based on Accounts. \n Partners: Prints report based on Partners."),
            'period_from': fields.many2one('account.period', 'Start Period'),
            'period_to': fields.many2one('account.period', 'End Period'),
            'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Account', required=True, domain=[('parent_id', '=', False)]),
            'company_id': fields.related('chart_account_id', 'company_id', type='many2one', relation='res.company', string='Company', readonly=True),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', required=True),
        }
    
    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False
    
    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        domain = [('date_start', '<', now), ('date_stop', '>', now)]
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
            domain += [('company_id', '=', company_id)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
    
    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {'value': {}}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False , 'date_to': False}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               ORDER BY p.date_start ASC, p.special ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res
    
    def onchange_coa(self, cr, uid, ids, chart_account_id, context=None):
        account_obj = self.pool.get('account.account') 
        res = {'value': {}}
        company_id = account_obj.browse(cr, uid, chart_account_id, context=context).company_id.id
        res['value'] = {'company_id': company_id}
        return res
    
    _defaults = {
        'account_ids': [],
        'partner_ids': [],
        'group_by': 'by_accounts',
        'filter': 'filter_no',
        'form_type': 'c_form',
        'chart_account_id': _get_account,
        'fiscalyear_id': _get_fiscalyear
    }
    
    def print_report(self, cr, uid, ids, context=None):
        """
         To get the date and print the report
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: return report
        """
        account_obj = self.pool.get('account.account')
        partner_obj = self.pool.get('res.partner')
        if context is None:
            context = {}
        res = self.read(cr, uid, ids, context=context)
        res = res and res[0] or {}
        group_by = res['group_by']
        if group_by == 'by_accounts':
            if res['account_ids']:
                ids_list = res['account_ids']
            else:
                ids_list = account_obj.search(cr, uid, [('type', 'in', ('receivable','payable')), ('company_id','=',res['company_id'][0])], context=context)
            datas = {
             'ids': ids_list,
             'model': 'account.account',
             'form': res
                 }
            
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'account.account.cform',
                'datas': datas,
           }
        else:
            if res['partner_ids']:
                ids_list = res['partner_ids']
            else:
                ids_list = partner_obj.search(cr, uid, [], context=context)
            datas = {
             'ids': ids_list,
             'model': 'res.partner',
             'form': res
                 }
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'res.partner.cform',
                'datas': datas,
           }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: