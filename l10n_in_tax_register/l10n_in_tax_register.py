# -*- encoding: utf-8 -*-
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
import xlwt
import base64
from operator import itemgetter
from itertools import groupby
from openerp.osv import fields,osv
from openerp.tools.translate import _
import format_common

class account_move_line_excel(osv.osv_memory):
    
    _name = 'account.move.line.excel'
    
    _columns = {
            'journal_ids': fields.many2many('account.journal', 'account_tax_report_journal_rel', 'account_id', 'journal_id', 'Journals', required=True),
            'filter': fields.selection([('filter_no', 'No Filters'), ('filter_period', 'Periods')], "Filter by", required=True),
            'period_from': fields.many2one('account.period', 'Start period'),
            'period_to': fields.many2one('account.period', 'End period'),
            'chart_account_id': fields.many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain=[('parent_id', '=', False)]),
            'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year', required=True),
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
                               AND p.special = false
                               ORDER BY p.date_start ASC, p.special ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res
    
    _defaults = {
        'journal_ids': [],
        'filter': 'filter_no',
        'chart_account_id': _get_account,
        'fiscalyear_id': _get_fiscalyear
    }
    
    def _get_header_values(self, cr, uid, journal_ids_tuple, period_ids_tuple, coa_id, fiscal_year_id, child_ids, filter):
        str_journal_ids_tuple = str(journal_ids_tuple)
        str_period_ids_tuple = str(period_ids_tuple)
        
        if len(journal_ids_tuple) == 1:
            str_journal_ids_tuple = str_journal_ids_tuple.replace(",", "") 
        if len(period_ids_tuple) == 1:
            str_period_ids_tuple = str_period_ids_tuple.replace(",", "") 
        if filter == 'filter_no':
            cr.execute(''' select distinct atc.name, at.parent_id 
                            from account_move_line aml
                            left join account_account aa on (aml.account_id = aa.id) 
                            left join account_account_type aat on (aat.id = aa.user_type) 
                            left join account_tax_code atc on (aml.tax_code_id = atc.id)
                            left join account_period ap on (aml.period_id = ap.id)
                            left join account_fiscalyear af on (ap.fiscalyear_id = af.id)
                            left join res_company rc on (aa.company_id = rc.id)
                            left join account_move am on (aml.move_id = am.id)
                            left join account_tax at on (at.tax_code_id = atc.id)
                            where aml.journal_id in %s and 
                            atc.name IS NOT NULL and aat.name in ('Liability','Tax Expense') and am.state = 'posted' and aa.id in %s and af.id = %s ''' % (str_journal_ids_tuple, tuple(child_ids), fiscal_year_id))
        else:    
            cr.execute(''' select distinct atc.name, at.parent_id 
                            from account_move_line aml
                            left join account_account aa on (aml.account_id = aa.id) 
                            left join account_account_type aat on (aat.id = aa.user_type) 
                            left join account_tax_code atc on (aml.tax_code_id = atc.id)
                            left join account_period ap on (aml.period_id = ap.id)
                            left join account_fiscalyear af on (ap.fiscalyear_id = af.id)
                            left join res_company rc on (aa.company_id = rc.id)
                            left join account_move am on (aml.move_id = am.id)
                            left join account_tax at on (at.tax_code_id = atc.id)
                            where aml.journal_id in %s and 
                            atc.name IS NOT NULL and aat.name in ('Liability','Tax Expense') and am.state = 'posted' and aa.id in %s and af.id = %s and aml.period_id in %s ''' % (str_journal_ids_tuple, tuple(child_ids), fiscal_year_id, str_period_ids_tuple))
        res = cr.dictfetchall()
        return res
    
    def _get_data(self, cr, journal_ids_tuple, period_ids_tuple, coa_id, fiscal_year_id, child_ids, filter):
        str_journal_ids_tuple = str(journal_ids_tuple)
        if len(journal_ids_tuple) == 1:
            str_journal_ids_tuple = str_journal_ids_tuple.replace(",", "") 
            
        str_period_ids_tuple = str(period_ids_tuple)
        if len(period_ids_tuple) == 1:
            str_period_ids_tuple = str_period_ids_tuple.replace(",", "") 
        if filter == 'filter_no':
            cr.execute('''select to_char(ai.date_invoice,'dd/mm/yyyy') as date_invoice, rp.name as consignee, rpp.name as partner_name, atc.name as tax_code , aml.tax_amount as tax_amount,
                          aj.name as journal_name, rpp.tin_no as tin_no, rpp.ecc_no as ecc_no,   
                          rpp.pan_no as pan_no, rpp.cst_no as cst_no, aml.move_id as move_id,
                          ai.number as retail_tax_no, ai.number as excise_number, aml.ref as reference, ai.amount_total as total, ai.amount_untaxed as base_amount
                          from account_move_line aml
                          left join account_account aa on (aml.account_id = aa.id) 
                          left join account_account_type aat on (aat.id = aa.user_type)  
                          left join account_journal aj on (aml.journal_id = aj.id)
                          left join account_tax_code atc on (aml.tax_code_id = atc.id) 
                          left join account_invoice ai on (aml.move_id = ai.move_id)
                          left join sale_order so on (ai.sale_id = so.id)
                          left join res_partner rp on (so.partner_shipping_id = rp.id)
                          left join res_partner rpp on (aml.partner_id = rpp.id)
                          left join account_period ap on (aml.period_id = ap.id)
                          left join account_fiscalyear af on (ap.fiscalyear_id = af.id)
                          left join res_company rc on (aa.company_id = rc.id)
                          left join account_move am on (aml.move_id = am.id)
                          where debit+credit  > 0.0 and tax_code_id is NOT NULL and 
                          aat.name in ('Liability','Tax Expense') and am.state = 'posted' and aml.journal_id in %s and aa.id in %s and af.id = %s order by move_id ''' % (str_journal_ids_tuple, tuple(child_ids), fiscal_year_id))
        else:     
            cr.execute('''select to_char(ai.date_invoice,'dd/mm/yyyy') as date_invoice, rp.name as consignee, rpp.name as partner_name, atc.name as tax_code , aml.tax_amount as tax_amount,
                          aj.name as journal_name, rpp.tin_no as tin_no, rpp.ecc_no as ecc_no,   
                          rpp.pan_no as pan_no, rpp.cst_no as cst_no, aml.move_id as move_id,
                          ai.number as retail_tax_no, ai.number as excise_number, aml.ref as reference, ai.amount_total as total, ai.amount_untaxed as base_amount
                          from account_move_line aml
                          left join account_account aa on (aml.account_id = aa.id) 
                          left join account_account_type aat on (aat.id = aa.user_type)  
                          left join account_journal aj on (aml.journal_id = aj.id)
                          left join account_tax_code atc on (aml.tax_code_id = atc.id) 
                          left join account_invoice ai on (aml.move_id = ai.move_id)
                          left join sale_order so on (ai.sale_id = so.id)
                          left join res_partner rp on (so.partner_shipping_id = rp.id)
                          left join res_partner rpp on (aml.partner_id = rpp.id)
                          left join account_period ap on (aml.period_id = ap.id)
                          left join account_fiscalyear af on (ap.fiscalyear_id = af.id)
                          left join res_company rc on (aa.company_id = rc.id)
                          left join account_move am on (aml.move_id = am.id)
                          where debit+credit  > 0.0 and tax_code_id is NOT NULL and 
                          aat.name in ('Liability','Tax Expense') and am.state = 'posted' and aml.journal_id in %s and aa.id in %s and af.id = %s and aml.period_id in %s order by move_id ''' % (str_journal_ids_tuple, tuple(child_ids), fiscal_year_id, str_period_ids_tuple))
        res = cr.dictfetchall()
        return res
    
    def _get_tax_codes(self, cr, uid, ids, context=None):
        account_move_line_obj = self.pool.get('account.move.line')
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_tax_obj = self.pool.get('account.invoice.tax')
        account_invoice_ids = []
        journals = ()
        for act_id in ids:
            period_from = self.browse(cr, uid, act_id, context=context).period_from.id
            period_to = self.browse(cr, uid, act_id, context=context).period_to.id
            journal_ids = self.browse(cr, uid, act_id, context=context).journal_ids
            filter = self.browse(cr, uid, act_id, context=context).filter
            for journal_id in journal_ids:
                journals = journals + (journal_id.id,)
        periods = ()
        periods = periods + (period_from,) + (period_to,)
        if filter == 'filter_no':
            move_line_ids = account_move_line_obj.search(cr, uid, [('journal_id', 'in', journals)], context=context)
        else:
            move_line_ids = account_move_line_obj.search(cr, uid, [('period_id', 'in', periods), ('journal_id', 'in', journals)], context=context)
        for move_line_id in move_line_ids:
            invoice_ids = account_move_line_obj.browse(cr, uid, move_line_id, context=context).invoice.id
            if invoice_ids:
                account_invoice_ids.append(invoice_ids)
        account_invoice_ids = list(set(account_invoice_ids))
        account_info = {}
        for account_invoice_id in account_invoice_ids:
            tax_codes = account_invoice_obj.browse(cr, uid, account_invoice_id, context=context).tax_line
            invoice_tax_name = account_invoice_obj.browse(cr, uid, account_invoice_id, context=context).number
            if tax_codes:
                tax_code_name = account_invoice_tax_obj.browse(cr, uid, tax_codes[0].id, context=context).tax_code_id.name
                account_info.update({invoice_tax_name:tax_code_name})
        return account_info
    
    def genarate_excel_report(self, cr, uid, ids, context=None):
        account_obj = self.pool.get('account.account')
        account_period_obj = self.pool.get('account.period')
        account_invoice_obj = self.pool.get('account.invoice')
        
        journal_ids_tuple = ()
        period_ids_tuple = ()
        if context is None:
            context={}
        for id in ids:
            journal_ids = self.browse(cr, uid, id, context=context).journal_ids
            start_period = self.browse(cr, uid, id, context=context).period_from.id
            stop_period = self.browse(cr, uid, id, context=context).period_to.id
            period_ids = account_period_obj.build_ctx_periods(cr, uid, start_period, stop_period)
            coa_id = self.browse(cr, uid, id, context=context).chart_account_id.id
            fiscal_year_id = self.browse(cr, uid, id, context=context).fiscalyear_id.id
            filter = self.browse(cr, uid, id, context=context).filter
        period_ids_tuple = tuple(period_ids)
        
        child_ids = account_obj._get_children_and_consol(cr, uid, coa_id)
        for val in journal_ids:
            journal_ids_tuple += (val.id,)
        final_dict = {}
        header_dict = {}
        
        new_header_dict = {}
        
        wrk_bk = xlwt.Workbook()
        wrk_sht = wrk_bk.add_sheet('Voucher')
        row = 1
        base_col = 12
        header_style = format_common.font_style(position='center',bold=1, fontos='black', font_height=180,color='grey')
        wrk_sht.write(0,0,'Date', header_style)
        final_dict.update({'Date':False})
        header_dict.update({'Date': 0})
        wrk_sht.write(0,1,'Particulars', header_style)
        final_dict.update({'Particulars':False})
        header_dict.update({'Particulars':1})
        wrk_sht.write(0,2,'Consignee', header_style)
        final_dict.update({'Consignee':False})
        header_dict.update({'Consignee':2})
        wrk_sht.write(0,3,'Excise Sr. No.', header_style)
        final_dict.update({'Excise Sr. No':False})
        header_dict.update({'Excise Sr. No':3})
        wrk_sht.write(0,4,'Tax/Retail Inv. No.', header_style)
        final_dict.update({'Tax/Retail Inv. No':False})
        header_dict.update({'Voucher No':4})
        wrk_sht.write(0,5,'Book Name', header_style)
        final_dict.update({'Book Name':False})
        header_dict.update({'Book Name':5})
        wrk_sht.write(0,6,'Voucher Ref', header_style)
        final_dict.update({'Voucher Ref':False})
        header_dict.update({'Voucher Ref':6})
        wrk_sht.write(0,7,'TIN/SALES Tax No.', header_style)
        final_dict.update({'TIN/SALES Tax No':False})
        header_dict.update({'TIN/SALES Tax No':7})
        wrk_sht.write(0,8,'Service Tax No.', header_style)
        final_dict.update({'Service Tax No':False})
        header_dict.update({'Service Tax No':8})
        wrk_sht.write(0,9,'Excise Reg. No.', header_style)
        final_dict.update({'Excise Reg. No':False})
        header_dict.update({'Excise Reg. No':9})
        wrk_sht.write(0,10,'PAN No.', header_style)
        final_dict.update({'PAN No':False})
        header_dict.update({'PAN No':10})
        wrk_sht.write(0,11,'CST No.', header_style)
        final_dict.update({'CST No':False})
        header_dict.update({'CST No':11})
#        wrk_sht.write(0,12,'Sales - CST 5%', header_style)
#        final_dict.update({'Sales - CST 5%':False})
#        header_dict.update({'Sales - CST 5%':12})
#        wrk_sht.write(0,13,'Sales - CST 2%', header_style)
#        final_dict.update({'Sales - CST 2%':False})
#        header_dict.update({'Sales - CST 2%':13})
        
        for i in range(12):
            wrk_sht.col(i).width = 256 * 30
            
        header_data = self._get_header_values(cr, uid, journal_ids_tuple, period_ids_tuple, coa_id, fiscal_year_id, child_ids, filter)
        for accounts in header_data:
            if accounts['name']:
                accounts['name'] = str(accounts['name'])
                if accounts['parent_id'] is None:
                    wrk_sht.write(0,base_col,accounts['name'] + ' - Base', header_style)
                    final_dict.update({accounts['name'] + ' - Base':False})
                    header_dict.update({accounts['name'] + ' - Base':base_col})
                    new_header_dict.update({base_col: accounts['name'] + ' - Base'})
                    
                    wrk_sht.col(base_col).width = 256 * 50
                    col = base_col + 1
                else:
                    col = base_col
                wrk_sht.write(0,col,accounts['name'], header_style)
                final_dict.update({accounts['name']:False})
                header_dict.update({accounts['name']:col})
                new_header_dict.update({col: accounts['name']})
            
                base_col = col + 1
                wrk_sht.col(col).width = 256 * 40
        wrk_sht.write(0,base_col,'Gross Total', header_style)
        wrk_sht.col(base_col).width = 256 * 20
        final_dict.update({'Gross Total':False})
        header_dict.update({'Gross Total':base_col})
        new_header_dict.update({base_col: 'Gross Total'})
        
        sorted_list = [x for x in new_header_dict.iteritems()]
        sorted_list.sort(key=lambda x: x[0])
        data = self._get_data(cr, journal_ids_tuple, period_ids_tuple, coa_id, fiscal_year_id, child_ids, filter)
        new_data = dict((k, [v for v in itr]) for k, itr in groupby(sorted(data, key=lambda x: x['move_id']), itemgetter('move_id')))
        get_tax_codes = self._get_tax_codes(cr, uid, ids, context=context)
        xyz = []
        
        for key in new_data:
            invoice_id = account_invoice_obj.search(cr, uid, [('move_id', '=', key)])
            if invoice_id:
                account_invoice_rec = account_invoice_obj.browse(cr, uid, invoice_id[0])
                tax_line = account_invoice_rec.tax_line
                if tax_line:
                    tax_base = tax_line[0].base
            tax_total = 0.0
            final_dict_child  = final_dict.copy()
            for val in new_data[key]:
                final_dict_child['Date'] = val['date_invoice']
                final_dict_child['Particulars'] = val['partner_name']
                final_dict_child['Consignee'] = val['consignee']
                final_dict_child['Excise Sr. No'] = val['excise_number']
                final_dict_child['Tax/Retail Inv. No'] = val['retail_tax_no']
                final_dict_child['Book Name'] = val['journal_name']
                final_dict_child['Voucher Ref'] = val['reference']
                final_dict_child['TIN/SALES Tax No'] = val['tin_no']
#                final_dict_child['Service Tax No'] = val['journal_name']
                final_dict_child['Excise Reg. No'] = val['ecc_no'] 
                final_dict_child['PAN No'] = val['pan_no']
                final_dict_child['CST No'] = val['cst_no']
                final_dict_child['CST No'] = val['cst_no']
                if val['tax_code'] in final_dict_child: 
                    final_dict_child[val['tax_code']] = val['tax_amount']
                    for key, value in get_tax_codes.items():
                        if str(key) == val['excise_number']:
                            new_value = str(value) + ' - Base'
                            if new_value in final_dict_child:
                                final_dict_child[new_value] = tax_base
                    tax_total+= val['tax_amount']
                    final_dict_child['Gross Total'] = val['total']
                    xyz.append(final_dict_child)
                    
        new_list = [i for n, i in enumerate(xyz) if i not in xyz[n + 1:]]
        for values in new_list:
            wrk_sht.write(row,0,values['Date'] or '')
            wrk_sht.write(row,1,values['Particulars'] or '')
            wrk_sht.write(row,2,values['Consignee'] or '')
            wrk_sht.write(row,3,values['Excise Sr. No'] or '')
            wrk_sht.write(row,4,values['Tax/Retail Inv. No'] or '')
            wrk_sht.write(row,5,values['Book Name'] or '')
            wrk_sht.write(row,6,values['Voucher Ref'] or '')
            wrk_sht.write(row,7,values['TIN/SALES Tax No'] or '')
            wrk_sht.write(row,8,values['Service Tax No'] or '')
            wrk_sht.write(row,9,values['Excise Reg. No'] or '')
            wrk_sht.write(row,10,values['PAN No'] or '')
            wrk_sht.write(row,11,values['CST No'] or '')
            for value in sorted_list:
                if values[value[1]]:
                    tax_total+= values[value[1]]
                if values[value[1]] is False:
                    wrk_sht.write(row,value[0],values[value[1]] or '')
                else:
                    wrk_sht.write(row,value[0],values[value[1]])
            row +=1
        
        wrk_bk.save('/tmp/voucher_receipt.xls')
        result_file = open('/tmp/voucher_receipt.xls','rb').read()
        context['name'] = 'voucher_receipt.xls'
        form_view = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'l10n_in_tax_register', 'view_wizard_msg_voucher')
        context['file'] = base64.encodestring(result_file)
        
        value = {
            'name': _('Notification'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.voucher.msg',
            'target':'new',
            'view_id': False,
            'views': [(form_view and form_view[1] or False, 'form')],
            'type': 'ir.actions.act_window',
        }
        return value
    
class wizard_voucher_msg(osv.osv_memory):
    _name = "wizard.voucher.msg"
    _description = "Wizard Message"
    _columns = {
        'msg': fields.char('File created',size=264, readonly=True),
        'report': fields.binary('Prepared file',filters='.xls', readonly=True), 
        'name': fields.char('File Name', size=32),
    }

    def default_get(self, cr, uid, fields, context):
        
        if context is None:
            context = {}
        res = {}
        if 'report' in fields and 'file' in context and 'name' in context:
            res.update({'report': context['file'], 'name':context['name']})
        return res
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:       
