
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com
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
###############################################################################

from osv import fields, osv
import pooler
from tools import config
import decimal_precision as dp
from tools.translate import _
import time

class account_invoice(osv.osv):
    _name="account.invoice"
    _inherit="account.invoice"

    def _get_invoice_from_line(self, cr, uid, ids, context=None):
        move = {}
        for line in self.pool.get('account.move.line').browse(cr, uid, ids, context=context):
            if line.reconcile_partial_id:
                for line2 in line.reconcile_partial_id.line_partial_ids:
                    move[line2.move_id.id] = True
            if line.reconcile_id:
                for line2 in line.reconcile_id.line_id:
                    move[line2.move_id.id] = True
        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids

    def _get_invoice_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile').browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True

        invoice_ids = []
        if move:
            invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('move_id','in',move.keys())], context=context)
        return invoice_ids
    
    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        result = {}
        
        print "amount residual called++++++++++++++++++++++++++inv.py"
        for invoice in self.browse(cr, uid, ids, context=context):
            tmp = 0.0
            result[invoice.id] = 0.0
            if invoice.move_id:
                for m in invoice.move_id.line_id:
                    print m.partner_id.name,"Partner name inv.py 96",m.account_id.name
                    print invoice.partner_id.name,"Invoice partner"
                    if m.account_id.type in ('receivable','payable'):                    
                         result[invoice.id] = m.amount_residual_currency
                    """
                         if m.partner_id != invoice.partner_id:                         
                                tmp  -= m.amount_residual_currency
                                print "In tmp1",tmp
                         else:
                                #Check if it goes to tds payable account and don't add it as that is payable against GOVT not for  invoiced customer
                                #if not m.account_id.tds_deductee_id:
                                if m.debit and m.name=='TDS Payable': #means tds payable, not for this partner
                                    print "TDS PAYBLE ACC dont add ****************************************"
                                    pass
                                else:                                    
                                    tmp  += m.amount_residual_currency
                                print "In tmp2",tmp
                         print m.amount_residual_currency,"amt inv.py ----------------------------"
                result[invoice.id] = tmp
                """
        return result


    def _amount_tds(self, cr, uid, ids, name, args, context={}):
        #id_set=",".join(map(str,ids))
        print "Amount TDS Called",ids
        res={}
        for inv in self.browse(cr,uid,ids):
            if inv.type=='in_invoice':                
                print "In invoice"
                for line in inv.invoice_line:
                    print "Inv line"
                    if line.tds_ids:
                        print "tds ids",line.tds_ids
                        for tds in line.tds_ids:
                            if tds.state!='later':
                                print "inv id tds value",tds.id,"->",tds.id
                                if res.has_key(inv.id):
                                        res[inv.id] += tds.tds_amount
                                else:
                                    res[inv.id] = tds.tds_amount
        return res
                
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'amount_tds':0.0
            }
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
                print line.tds_ids,"--tds ids amt_all"
                if line.tds_ids:
                        print "tds ids",line.tds_ids
                        for tds in line.tds_ids:
                            print tds.tds_amount,"--tds amt"
                            if tds.state!='later': #later state need to be ignored
                                res[invoice.id]['amount_tds']  += float(tds.tds_amount)
                
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed'] - res[invoice.id]['amount_tds']
        print res,"---RRRRRRRRRR"
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def action_move_create(self, cr, uid, ids, *args):
        """Creates invoice related analytics and financial move lines, hacking to add TDS support"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        context = {}
        for inv in self.browse(cr, uid, ids):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error !'), _('Please define sequence on invoice journal'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines !'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice':time.strftime('%Y-%m-%d')})
            company_currency = inv.company_id.currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id)
            # check if taxes are all computed
            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
                raise osv.except_osv(_('Bad total !'), _('Please verify the price of the invoice !\nThe real total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error !'), _("Cannot create the invoice !\nThe payment term defined gives a computed amount greater than the total invoiced amount."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml)
            acc_id = inv.account_id.id

            name = inv['name'] or '/'
            totlines = False
            if inv.payment_term:
                totlines = self.pool.get('account.payment.term').compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid,
                                company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and  amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            part = inv.partner_id.id

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, context={})),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                        _('Cannot create invoice move on centralised journal'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'type': entry_type,
                'narration':inv.comment
            }
            period_id = inv.period_id and inv.period_id.id or False
            if not period_id:
                period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',inv.date_invoice or time.strftime('%Y-%m-%d')),('date_stop','>=',inv.date_invoice or time.strftime('%Y-%m-%d')), ('company_id', '=', inv.company_id.id)])
                if period_ids:
                    period_id = period_ids[0]
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id
            #selvam starts
            if inv.type=="in_invoice":
              tds_obj = self.pool.get('account.tds')
              print "In invoice 251 acc_inv_tds.py"
              #get govt supplier id, assume its name id 'GOVT'
              part_obj = self.pool.get('res.partner')
              govt_ids = part_obj.search(cr,uid,[('name','=','GOVT')])
              if not govt_ids:
                raise osv.except_osv(_('Error !'), _('You need to have a supplier with name="GOVT" for encoding TDS against govt. '))
              for inv_line in inv.invoice_line:                
                  if inv_line.tds_ids:
                     for tds in inv_line.tds_ids:
                        if tds.state=='draft':#'later' state will not be accounted now                             
                            print tds.tds_nature_id.account_id.id,"--acc id",inv.partner_id.id
                            tmp=(0, 0, {'analytic_account_id': False, 'tax_code_id': False, 'analytic_lines': [],                         
                            'tax_amount': 0.0,                        
                            'name': u'TDS Expense', 'ref': '', 'journal_id': inv.journal_id.id,
                             'currency_id': False, 'credit':float(tds.tds_amount), 'product_id':False, 
                             'date_maturity': False, 'period_id':period_id , 'debit':0.0 ,
                              'date': date, 'amount_currency': 0, 'product_uom_id': False, 'quantity':False,
                               'partner_id':govt_ids[0], 'account_id':tds.tds_nature_id.account_id.id,'tds_id':tds.id }) 
                            move['line_id'].append(tmp)

                            """ reduce from original move line"""
                            tmp = move['line_id']
                            for i,ml in enumerate(move['line_id']):
                                print ml,"MLML",ml[2]['partner_id'],inv.partner_id.id
                                if ml[2]['partner_id'] == inv.partner_id.id and ml[2]['credit']:
                                    #reducing tds amount from payable
                                    print "REDUCING RRRRRRRRRRRRRRRRRRRRR",tmp[i][2]['credit']
                                    tmp[i][2]['credit'] -= float(tds.tds_amount)
                            move['line_id'] = tmp
                            """
                            tmp=(0, 0, {'analytic_account_id': False, 'tax_code_id': False, 'analytic_lines': [],                         
                            'tax_amount': 0.0,                        
                            'name': u'TDS Payable', 'ref': '', 'journal_id': inv.journal_id.id,
                             'currency_id': False, 'credit':0.0, 'product_id':False, 
                             'date_maturity': False, 'period_id':period_id , 'debit':float(tds.tds_amount) ,
                              'date': date, 'amount_currency': 0, 'product_uom_id': False, 'quantity':False,
                               'partner_id':inv.partner_id.id, 'account_id':inv.account_id.id,'tds_id':tds.id }) 
                            move['line_id'].append(tmp)
                            """
                            
                            tds_obj.write(cr,uid,[tds.id],{'state':'confirmed'})

            #selvam ends        
                    
                    
                    
                    

            move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
            new_move_name = self.pool.get('account.move').browse(cr, uid, move_id).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name})
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            self.pool.get('account.move').post(cr, uid, [move_id], context={'invoice':inv})
        self._log_event(cr, uid, ids)
        return True



    


    _columns={
        'amount_untaxed': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 20),
            },
            multi='all'),

        #selvam adds next field
        'amount_tds':fields.function(_amount_tds,method=True,type="float",string="TDS Amount",        
          store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 50),                
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
                
            },
        
        ), 
        
        'residual': fields.function(_amount_residual, method=True, digits_compute=dp.get_precision('Account'), string='Residual',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['invoice_line'], 50),
                'account.invoice.tax': (_get_invoice_tax, None, 50),
                'account.invoice.line': (_get_invoice_line, ['price_unit','invoice_line_tax_id','quantity','discount','invoice_id'], 50),
                'account.move.line': (_get_invoice_from_line, None, 50),
                'account.move.reconcile': (_get_invoice_from_reconcile, None, 50),
            },
            help="Remaining amount due."),       

       }
account_invoice()
