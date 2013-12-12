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
from report import report_sxw

class c_form_report(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(c_form_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_data': self.get_data,
        })
        
    def get_data(self, partner_id, form):
        account_invoice_obj = self.pool.get('account.invoice')
        account_period_obj = self.pool.get('account.period')
        
        cform_data_list = []
        
        start_period = form['period_from'] and form['period_from'][0]
        stop_period = form['period_to'] and form['period_to'][0]
        group_by = form['group_by']
        filter_by = form['filter']
        form_type = form['form_type']
        fiscalyear_id = form['fiscalyear_id'][0]
        company_id = form['company_id'][0]
        if start_period and not stop_period:
            stop_period = account_period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id)], order='date_stop desc', limit=1)[0]
            
        period_ids = account_period_obj.build_ctx_periods(self.cr, self.uid, start_period, stop_period)
        
        if filter_by == 'filter_no':
            invoice_ids = account_invoice_obj.search(self.cr, self.uid, [('partner_id', '=', partner_id), ('form_type', '=', form_type), ('state', 'not in', ['draft', 'cancel']), ('company_id','=', company_id)])
        else:
            invoice_ids = account_invoice_obj.search(self.cr, self.uid, [('partner_id', '=', partner_id), ('period_id', 'in', period_ids), ('form_type', '=', form_type), ('state', 'not in', ['draft', 'cancel']), ('company_id','=', company_id)])
        for invoice_id in invoice_ids:
            account_invoice_rec = account_invoice_obj.browse(self.cr, self.uid, invoice_id)
            if group_by == 'by_accounts':
                name = account_invoice_rec.partner_id.name
            form_type = account_invoice_rec.form_type
            
            invoice_date = account_invoice_rec.date_invoice
            cst_no = account_invoice_rec.partner_id.cst_no
            amount_total = account_invoice_rec.amount_total
            form_no = account_invoice_rec.form_no
            form_date = account_invoice_rec.form_date
            number = account_invoice_rec.number
            voucher_type = account_invoice_rec.journal_id.name
            tax_line_ids = account_invoice_rec.tax_line
            
            for tax_line_id in tax_line_ids:
                if tax_line_id.tax_categ == 'cst':
                    if group_by == 'by_partners':
                        name = tax_line_id.name
                    cst_amount = tax_line_id.amount
                    assessable_value = tax_line_id.base
                    
                    cform_data_list.append({'invoice_date': invoice_date, 'name': name, 'cst_no': cst_no, 'number': number, 
                                                     'assessable_value': assessable_value, 'cst_amount': cst_amount, 
                                                     'amount_total': amount_total, 'form_type': form_type, 'form_no': form_no, 
                                                     'form_date': form_date, 'voucher_type': voucher_type})
        return cform_data_list
    
report_sxw.report_sxw('report.res.partner.cform', 'res.partner', 'addons/l10n_in_cform/report/cform.rml', parser=c_form_report, header='internal')

class c_form_report_accounts(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context=None):
        super(c_form_report_accounts, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_data': self.get_data,
        })
        
    def get_data(self, account_id, form):
        account_invoice_obj = self.pool.get('account.invoice')
        account_period_obj = self.pool.get('account.period')
        
        cform_data_list = []
        start_period = form['period_from'] and form['period_from'][0]
        stop_period = form['period_to'] and form['period_to'][0]
        group_by = form['group_by']
        filter_by = form['filter']
        form_type = form['form_type']
        fiscalyear_id = form['fiscalyear_id'][0]
        company_id = form['company_id'][0]
        
        if start_period and not stop_period:
            stop_period = account_period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id)], order='date_stop desc', limit=1)[0]
        
        period_ids = account_period_obj.build_ctx_periods(self.cr, self.uid, start_period, stop_period)
        if filter_by == 'filter_no':
            invoice_ids = account_invoice_obj.search(self.cr, self.uid, [('account_id', '=', account_id), ('form_type', '=', form_type), ('state', 'not in', ['draft', 'cancel']), ('company_id','=', company_id)])
        else:
            invoice_ids = account_invoice_obj.search(self.cr, self.uid, [('account_id', '=', account_id), ('period_id', 'in', period_ids), ('form_type', '=', form_type), ('state', 'not in', ['draft', 'cancel']), ('company_id','=', company_id)])
        for invoice_id in invoice_ids:
            account_invoice_rec = account_invoice_obj.browse(self.cr, self.uid, invoice_id)
            if group_by == 'by_accounts':
                name = account_invoice_rec.partner_id.name
            form_type = account_invoice_rec.form_type
            
            invoice_date = account_invoice_rec.date_invoice
            cst_no = account_invoice_rec.partner_id.cst_no
            amount_total = account_invoice_rec.amount_total
            form_no = account_invoice_rec.form_no
            form_date = account_invoice_rec.form_date
            number = account_invoice_rec.number
            voucher_type = account_invoice_rec.journal_id.name
            tax_line_ids = account_invoice_rec.tax_line
            
            for tax_line_id in tax_line_ids:
                if tax_line_id.tax_categ == 'cst':
                    if group_by == 'by_partners':
                        name = tax_line_id.name
                    cst_amount = tax_line_id.amount
                    assessable_value = tax_line_id.base
                    cform_data_list.append({'invoice_date': invoice_date, 'name': name, 'cst_no': cst_no, 'number': number, 
                                                     'assessable_value': assessable_value, 'cst_amount': cst_amount, 
                                                     'amount_total': amount_total, 'form_type': form_type, 'form_no': form_no, 
                                                     'form_date': form_date, 'voucher_type': voucher_type})
        return cform_data_list
    
report_sxw.report_sxw('report.account.account.cform', 'account.account', 'addons/l10n_in_cform/report/cform.rml', parser=c_form_report_accounts, header='internal')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: