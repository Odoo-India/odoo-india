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
import json
import httplib
import logging

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

PURTRAN = """INSERT INTO [MZFAS].[dbo].[PURTRAN] ([COCODE], [FINYEAR], [BKTYPE], [VOUNO], [VOUSRL], [SERIES], [RMQTY], [PAYDUE], [STCODE], [TAXAMT], [GSTAMT], [STAMT], [SURAMT], [USERID], [ACTION], [PRTFLG], [ADVAMT], [DEDACCODE1], [DEDAMT1], [DEDACCODE2], [DEDAMT2], [RETAMT],  [DEBAMT], [DEBVOUNO], [DEBVATAMT], [RSNCODE], [STAMT1], [STAMT2], [DEBVATAMT1], [DEBVATAMT2], [EXCISE], [EXCISECESS], [EXCISEHCESS], [RATE], [CFORMIND], [STATE], [REASON], [CONRETAMT], [DEDACCODE3], [DEBTAXABLEAMT], [AHDFLG], [DEDACCODE4], [DEDAMT4])
         VALUES ('%(COCODE)s',  '%(FINYEAR)s',  '%(BKTYPE)s',  '%(VOUNO)s',  '%(VOUSRL)s',  '%(SERIES)s',  '%(RMQTY)s',  '%(PAYDUE)s',  '%(STCODE)s',  '%(TAXAMT)s',  '%(GSTAMT)s',  '%(STAMT)s',  '%(SURAMT)s',  '%(USERID)s',  '%(ACTION)s', '%(PRTFLG)s',  '%(ADVAMT)s',  '%(DEDACCODE1)s',  '%(DEDAMT1)s',  '%(DEDACCODE2)s',  '%(DEDAMT2)s',  '%(RETAMT)s',  '%(DEBAMT)s',  '%(DEBVOUNO)s',  '%(DEBVATAMT)s', '%(RSNCODE)s', '%(STAMT1)s', '%(STAMT2)s',  '%(DEBVATAMT1)s',  '%(DEBVATAMT2)s',  '%(EXCISE)s',  '%(EXCISECESS)s',  '%(EXCISEHCESS)s',  '%(RATE)s',  '%(CFORMIND)s',  '%(STATE)s',  '%(REASON)s',  '%(CONRETAMT)s',  '%(DEDACCODE3)s',  '%(DEBTAXABLEAMT)s',  '%(AHDFLG)s',  '%(DEDACCODE4)s',  '%(DEDAMT4)s')"""

TRANMAIN = """INSERT INTO [MZFAS].[dbo].[TRANMAIN] ([COCODE], [FINYEAR], [BKTYPE], [BKSRS], [VOUNO], [VOUSRL], [VOUDATE], [VOUSTS], [FASCODE], [CRDBID],  [VOUAMT], [SUBCODE], [REFNO], [REFDAT], [REMK01], [REMK02], [REMK03], [REMK04], [USERID], [ACTION], [CVOUNO])
            VALUES ('%(COCODE)s', '%(FINYEAR)s', '%(BKTYPE)s', '%(BKSRS)s', '%(VOUNO)s', '%(VOUSRL)s', '%(VOUDATE)s', '%(VOUSTS)s', '%(FASCODE)s', '%(CRDBID)s', '%(VOUAMT)s', '%(SUBCODE)s', '%(REFNO)s', '%(REFDAT)s', '%(REMK01)s', '%(REMK02)s', '%(REMK03)s', '%(REMK04)s', '%(USERID)s', '%(ACTION)s', '%(CVOUNO)s')"""

BANKTRAN = """INSERT INTO [MZFAS].[dbo].[BANKTRAN] ([COCODE], [FINYEAR], [BKTYPE], [VOUNO], [VOUSRL], [BANKCD], [CHQDRF], [CHDRNO], [CHDRDT], [PRTFLG], [USERID], [ACTION], [CONTRABANKCD], [CONTRAVOUNO], [CONTRAFASCODE], [chqinfavour], [PAYABLEAT], [CVOUNO])
            VALUES ('%(COCODE)s', '%(FINYEAR)s', '%(BKTYPE)s', '%(VOUNO)s', '%(VOUSRL)s', '%(BANKCD)s', '%(CHQDRF)s', '%(CHDRNO)s', '%(CHDRDT)s', '%(PRTFLG)s', '%(USERID)s', '%(ACTION)s', '%(CONTRABANKCD)s', '%(CONTRAVOUNO)s', '%(CONTRAFASCODE)s', '%(chqinfavour)s', '%(PAYABLEAT)s', '%(CVOUNO)s)"""

_logger = logging.getLogger(__name__)

class account_invoice(osv.Model):
    _inherit = "account.invoice"
    
    def invoice_validate(self, cr, uid, ids, context=None):
        super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        invoice = self.browse(cr, uid, ids, context=context)[0]
        if invoice.company_id.account_ip and invoice.company_id.account_port:
            self._create_voucher(cr, uid, invoice, context=context)
        else:
            _logger.error("Accounting server location not defined !")
        return True
    
    def _execute_sql(self, cr, uid, invoice, sql, vals, context):
        headers = {
           "Content-type": "application/x-www-form-urlencoded", 
           "Accept": "text/json"
        }
        url = "%s:%s" % (invoice.company_id.account_ip, invoice.company_id.account_port)
        conn = httplib.HTTPConnection(url)
        data = False
        if invoice.company_id.account_ip:
            sql = sql % vals
            try:
                conn.request("GET", "/cgi-bin/query", sql, headers)
                rsp = conn.getresponse()
                data_received = rsp.read()
                data = json.loads(data_received)
                _logger.info("SQL Execute : %s", sql)
            except Exception:
                _logger.error("SQL Execute failed : %s", sql)
        return data
    
    def _get_voucher_number(self, cr, uid, invoice, debit_note=False, context=None):
        voucher_no = invoice.maize_voucher_no
        
        if (not debit_note) and voucher_no:
            return voucher_no

        current_month = time.strptime(invoice.date_invoice,'%Y-%m-%d').tm_mon
        cls_dict = {'1':'01', '2':'02', '3':'03', '4':'04', '5':'05', '6':'06', '7':'07', '8':'08', '9':'09', '10':'10', '11':'11', '12':'12'}
        close_column = "CLS%s" % (cls_dict.get(str(current_month)))
        month_column = "VOUNO%s" % (cls_dict.get(str(current_month)))
        
        journal = ''
        if invoice.move_id.journal_id.type == 'purchase':
            journal = 'PUR'

        vounoSQL = ""
        if debit_note:
            journal = 'DBN'
            vounoSQL = "SELECT [%s] as IS_OPEN, [VOUNO] as VOUNO FROM [MZFAS].[dbo].[FASPARM] where COCODE='1' and FINYEAR=%s and TYPE='DBK' and SUBTYPE='%s'  and SERIES='ZZ'" % (close_column, invoice.move_id.period_id.fiscalyear_id.name, journal)
        else:
            vounoSQL = "SELECT [%s] as IS_OPEN, [%s] as VOUNO  FROM [MZFAS].[dbo].[FASPARM] where COCODE='1' and FINYEAR=%s and TYPE='DBK' and SUBTYPE='%s' and SERIES='%s'" % (close_column, month_column, invoice.move_id.period_id.fiscalyear_id.name, journal, invoice.move_id.journal_id.series)

        data = self._execute_sql(cr, uid, invoice, vounoSQL, {}, context)
        is_open = data[0]['IS_OPEN']
        voucher_no = int(data[0]['VOUNO']) + 1

        if not debit_note and is_open == 'Y':
            raise osv.except_osv(_('Error !'), _('Accounting period closed for %s date, please contact to Account / EDP Department !' % (invoice.date_invoice) ))

        if debit_note:
            journal = 'DBN'
            vounoSQL = "UPDATE [MZFAS].[dbo].[FASPARM] SET [VOUNO]=%s where COCODE='1' and FINYEAR=%s and TYPE='DBK' and SUBTYPE='%s' and SERIES='ZZ'" % (voucher_no, invoice.move_id.period_id.fiscalyear_id.name, journal)
        else:
            vounoSQL = "UPDATE [MZFAS].[dbo].[FASPARM] SET [%s]=%s where COCODE='1' and FINYEAR=%s and TYPE='DBK' and SUBTYPE='%s' and SERIES='%s'" % (month_column, voucher_no, invoice.move_id.period_id.fiscalyear_id.name, journal, invoice.move_id.journal_id.series)

        data = self._execute_sql(cr, uid, invoice, vounoSQL, {}, context)
        
        return voucher_no
    
    def _get_transaction_line(self, cr, uid, invoice, debit_note=False, context=None):
        '''
        It will init by defaults when you need to create a transaction line, 
        when you need to set is just below 4 parameters only
        
        VOUNO': voucher_no
        VOUSRL': 0, 1, 2, 3
        CRDBID':C or D
        VOUAMT':amount
        '''
        
        BKTYPE = ""
        REFDAT = invoice.ref_date or ''
        ACTION = invoice.invoice_line and invoice.invoice_line[0].account_analytic_id.id or ''
        USERID = invoice.user_id and invoice.user_id.user_code[:3]
        
        if debit_note:
            BKTYPE = 'DBP'
        else:
            BKTYPE = invoice.move_id.journal_id.maize_code or ''
        
        res = {
            'COCODE': 1,
            'FINYEAR': invoice.period_id.fiscalyear_id.name or '',
            'BKTYPE': BKTYPE,
            'BKSRS': invoice.move_id.journal_id.series and invoice.move_id.journal_id.series  or '',
            'VOUDATE': invoice.date_invoice,
            'VOUSTS': '',
            'SUBCODE': '',
            'REFNO': invoice.supplier_invoice_number or '',
            'REFDAT': REFDAT,
            'REMK01': invoice.number + ':' + REFDAT,
            'REMK02': '',
            'REMK03': '',
            'REMK04': '',
            'USERID': 'ERP' + '/' + USERID or '',
            'ACTION': ACTION,
            'CVOUNO': 0,
        }
        return res

    def _create_debit_note(self, cr, uid, invoice, context=None):
        voucher_no = self._get_voucher_number(cr, uid, invoice, True, context=context)
        self.write(cr, uid, [invoice.id], {'debit_note_no': voucher_no}, context=context)
        cr.commit()

        tax_exist = False
        for tax in invoice.tax_line:
            if tax.tax_categ in ('vat', 'add_vat'):
                tax_exist = True
                break

        ref_date = invoice.ref_date or ''

        debit_line = str(TRANMAIN)
        debit_vals = self._get_transaction_line(cr, uid, invoice, True, context)
        debit_vals.update({
            'VOUNO': voucher_no,
            'FASCODE': '302K060',
            'VOUSRL': 0,
            'REMK01': invoice.number + ':' + ref_date,
            'CRDBID':'D',
            'VOUAMT':invoice.debit_note_amount_total,
        })
        self._execute_sql(cr, uid, invoice, debit_line, debit_vals, context)

        credit_line = str(TRANMAIN)
        credit_vals = self._get_transaction_line(cr, uid, invoice, True, context)
        credit_vals.update({
            'VOUNO': voucher_no,
            'VOUSRL': 1,
            'FASCODE': '6102002',
            'REMK01': invoice.number + ':' + ref_date,
            'CRDBID':'C',
        })

        if tax_exist:
            credit_vals.update({'VOUAMT': invoice.debit_note_amount_total - (invoice.deb_vat + invoice.deb_add_vat)})
        else:
            credit_vals.update({'VOUAMT': invoice.debit_note_amount_total})

        self._execute_sql(cr, uid, invoice, credit_line, credit_vals, context)

        if tax_exist:
            tax_line = str(TRANMAIN)
            tax_vals = self._get_transaction_line(cr, uid, invoice, True, context)
            tax_vals.update({
                'VOUNO': voucher_no, 
                'VOUSRL': 2, 
                'FASCODE': '6102002',
                'REMK01': invoice.number + ':' + ref_date,
                'CRDBID':'C',
                'VOUAMT': invoice.deb_vat + invoice.deb_add_vat,
            })
            self._execute_sql(cr, uid, invoice, tax_line, tax_vals, context)

        return voucher_no
    
    def _create_voucher(self, cr, uid, invoice, context=None):
        #get next voucher number and store on invoice
        voucher_no = self._get_voucher_number(cr, uid, invoice, False, context=context)
        self.write(cr, uid, [invoice.id], {'maize_voucher_no': voucher_no}, context=context)
        cr.commit()
        
        #read invoice again, with the updated voucher number
        invoice = self.browse(cr, uid, invoice.id, context=context)

        #read tax amount and split in different types of tax applied on invoice.
        vat = add_vat = excise = cess = hedu = 0
        for tax in invoice.tax_line:
            if tax.tax_categ in ('vat'):
                vat += tax.amount
            elif tax.tax_categ in ('add_vat'):
                add_vat += tax.amount
            elif tax.tax_categ in ('excise'):
                excise += tax.amount
            elif tax.tax_categ in ('cess'):
                cess += tax.amount
            elif tax.tax_categ in ('hedu_cess'):
                hedu += tax.amount

        #compute and create a debit-notes before creating the voucher
        vat_debit = 0.0
        add_vat_debit = 0.0
        debit_note_id = 0
        if invoice.debit_note_amount_total:
            vat_debit = invoice.deb_vat
            add_vat_debit = invoice.deb_add_vat
            debit_note_id = self._create_debit_note(cr, uid, invoice, context=context)
        
        #copy the sql from PURTRAN
        purchaseSQL = str(PURTRAN)

        amount_total = invoice.debit_note_amount_total + invoice.retention_amount + invoice.advance_amount
        prtflag = ''
        if invoice.amount_total == amount_total:
            prtflag = 'P'

        user = invoice.user_id and invoice.user_id.user_code[:3]
        ref_date = str(invoice.ref_date) or ''

        taxamt = invoice.amount_total + invoice.rounding_shortage - (vat + add_vat)
        stamt = vat + add_vat
        suramt = invoice.amount_total - taxamt
        suramt = round(suramt - stamt,2)
        
        purchaseVals = {
            'COCODE': 1,
            'FINYEAR': invoice.move_id.period_id.fiscalyear_id.name or '',
            'BKTYPE': invoice.move_id.journal_id.maize_code or '',
            'VOUNO': voucher_no,
            'VOUSRL': 0,
            'SERIES': invoice.move_id.journal_id.series or '',
            'RMQTY': 0,
            'PAYDUE': invoice.date_due,
            'STCODE': invoice.st_code or '',
            'TAXAMT': taxamt,
            'GSTAMT': 0,
            'STAMT': stamt,
            'SURAMT': suramt,
            'USERID': 'ERP' + '/' + user or '',
            'ACTION': '',
            'PRTFLG': prtflag,
            'ADVAMT': invoice.advance_amount,
            'DEDACCODE1': invoice.tds_ac_code or '',
            'DEDAMT1': invoice.tds_amount,
            'DEDACCODE2': invoice.other_ac_code or '',
            'DEDAMT2': invoice.other_amount,
            'RETAMT': invoice.retention_amount,
            'DEBAMT': invoice.debit_note_amount_total,
            'DEBVOUNO': debit_note_id,
            'DEBVATAMT': vat_debit + add_vat_debit,
            'RSNCODE': invoice.invoice_line[0].reason or '',
            'STAMT1': vat,
            'STAMT2': add_vat,
            'DEBVATAMT1': vat_debit,
            'DEBVATAMT2': add_vat_debit,
            'EXCISE': '',
            'EXCISECESS': '',
            'EXCISEHCESS': '',
            'RATE': 0,
            'CFORMIND': invoice.c_form and 'Y' or 'N',
            'STATE': invoice.state_id and invoice.state_id.name or '',
            'REASON': invoice.invoice_line[0].reason or '',
            'CONRETAMT': 0,
            'DEDACCODE3': '',
            'DEBTAXABLEAMT': invoice.debit_note_amount_total - (vat_debit + add_vat_debit),
            'AHDFLG': '',
            'DEDACCODE4': '',
            'DEDAMT4' : 0,
        }

        self._execute_sql(cr, uid, invoice, purchaseSQL, purchaseVals, context)
        
        credit_lineSQL = str(TRANMAIN)
        credit_res = self._get_transaction_line(cr, uid, invoice, False, context)
        credit_res.update({
            'VOUNO': voucher_no,
            'VOUSRL': 0,
            'REMK01': 'Ref:' + str(invoice.number) + ':' + ref_date,
            'CRDBID':'C',
            'FASCODE':invoice.partner_id.supp_code,
            'VOUAMT':invoice.amount_total,
        })

        debit_lineSQL = str(TRANMAIN)
        debit_res = self._get_transaction_line(cr, uid, invoice, False, context)
        debit_res.update({
            'VOUNO': voucher_no,
            'VOUSRL': 1,
            'REMK01': 'Purchase Summary',
            'CRDBID':'D',
            'FASCODE':invoice.journal_id.default_debit_account_id.code,
            'VOUAMT':invoice.amount_total - invoice.other_amount,
        })

        self._execute_sql(cr, uid, invoice, credit_lineSQL, credit_res, context)
        self._execute_sql(cr, uid, invoice, debit_lineSQL, debit_res, context)

        if invoice.other_amount > 0:
            other_lineSQL = str(TRANMAIN)
            other_res = self._get_transaction_line(cr, uid, invoice, False, context)
            other_res.update({
                'VOUNO': voucher_no,
                'VOUSRL': 2,
                'CRDBID':'D',
                'FASCODE':invoice.other_ac_code,
                'VOUAMT':invoice.other_amount,
            })
            self._execute_sql(cr, uid, invoice, other_lineSQL, other_res, context)
        
account_invoice()