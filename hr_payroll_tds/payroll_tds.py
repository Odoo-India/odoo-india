from osv import fields, osv
from datetime import date, timedelta
import time

def prev_bounds(cdate=False):
    when = date.fromtimestamp(time.mktime(time.strptime(cdate,"%Y-%m-%d")))
    this_first = date(when.year, when.month, 1)
    month = when.month + 1
    year = when.year
    if month > 12:
        month = 1
        year += 1
    next_month = date(year, month, 1)
    prev_end = next_month - timedelta(days=1)
    return this_first, prev_end

class payroll_tds(osv.osv):
    """
    Adds a tds check box to salary heads.
    """
    _name = _inherit = 'hr.allounce.deduction.categoty'
    _columns = {
        'tds':fields.boolean('TDS ?',help="Is it a TDS deduction ?"),
        'tds_nature_id':fields.many2one("account.tds.nature","Nature of payment")
    }
payroll_tds()    

class hr_payslip(osv.osv):
    _name=_inherit = 'hr.payslip'
    
    def verify_sheet(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        movel_pool = self.pool.get('account.move.line')
        exp_pool = self.pool.get('hr.expense.expense')
        fiscalyear_pool = self.pool.get('account.fiscalyear')
        period_pool = self.pool.get('account.period')
        property_pool = self.pool.get('ir.property')
        payslip_pool = self.pool.get('hr.payslip.line')
        tds_pool = self.pool.get('account.tds')
        tds_line_pool = self.pool.get('account.tds.line')

        for slip in self.browse(cr, uid, ids, context=context):
            if not slip.journal_id:
                # Call super method to verify sheet if journal_id is not specified.
                super(hr_payslip, self).verify_sheet(cr, uid, [slip.id], context=context)
                continue
            total_deduct = 0.0

            line_ids = []
            partner = False
            partner_id = False

            if not slip.employee_id.bank_account_id:
                raise osv.except_osv(_('Configuration Error !'), _('Please define bank account for %s !') % (slip.employee_id.name))

            if not slip.employee_id.bank_account_id.partner_id:
                raise osv.except_osv(_('Configuration Error !'), _('Please define partner in bank account for %s !') % (slip.employee_id.name))

            partner = slip.employee_id.bank_account_id.partner_id
            partner_id = slip.employee_id.bank_account_id.partner_id.id

            period_id = False

            if slip.period_id:
                period_id = slip.period_id.id
            else:
                fiscal_year_ids = fiscalyear_pool.search(cr, uid, [], context=context)
                if not fiscal_year_ids:
                    raise osv.except_osv(_('Warning !'), _('Please define fiscal year for perticular contract'))
                fiscal_year_objs = fiscalyear_pool.read(cr, uid, fiscal_year_ids, ['date_start','date_stop'], context=context)
                year_exist = False
                for fiscal_year in fiscal_year_objs:
                    if ((fiscal_year['date_start'] <= slip.date) and (fiscal_year['date_stop'] >= slip.date)):
                        year_exist = True
                if not year_exist:
                    raise osv.except_osv(_('Warning !'), _('Fiscal Year is not defined for slip date %s') % slip.date)
                search_periods = period_pool.search(cr,uid,[('date_start','<=',slip.date),('date_stop','>=',slip.date)], context=context)
                if not search_periods:
                    raise osv.except_osv(_('Warning !'), _('Period is not defined for slip date %s') % slip.date)
                period_id = search_periods[0]

            move = {
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
                'date': slip.date,
                'ref':slip.number,
                'narration': slip.name
            }
            move_id = move_pool.create(cr, uid, move, context=context)
            self.create_voucher(cr, uid, [slip.id], slip.name, move_id)
            
            if not slip.employee_id.salary_account.id:
                raise osv.except_osv(_('Warning !'), _('Please define Salary Account for %s.') % slip.employee_id.name)
            
            line = {
                'move_id':move_id,
                'name': "By Basic Salary / " + slip.employee_id.name,
                'date': slip.date,
                'account_id': slip.employee_id.salary_account.id,
                'debit': slip.basic,
                'credit': 0.0,
                'quantity':slip.working_days,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
                'analytic_account_id': False,
                'ref':slip.number
            }
            #Setting Analysis Account for Basic Salary
            if slip.employee_id.analytic_account:
                line['analytic_account_id'] = slip.employee_id.analytic_account.id

            move_line_id = movel_pool.create(cr, uid, line, context=context)
            line_ids += [move_line_id]

            if not slip.employee_id.employee_account.id:
                raise osv.except_osv(_('Warning !'), _('Please define Employee Payable Account for %s.') % slip.employee_id.name)
            
            line = {
                'move_id':move_id,
                'name': "To Basic Payable Salary / " + slip.employee_id.name,
                'partner_id': partner_id,
                'date': slip.date,
                'account_id': slip.employee_id.employee_account.id,
                'debit': 0.0,
                'quantity':slip.working_days,
                'credit': slip.basic,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
                'ref':slip.number
            }
            
            line_ids += [movel_pool.create(cr, uid, line, context=context)]

            for line in slip.line_ids:
                name = "[%s] - %s / %s" % (line.code, line.name, slip.employee_id.name)
                amount = line.total

                if line.type == 'leaves':
                    continue

                rec = {
                    'move_id': move_id,
                    'name': name,
                    'date': slip.date,
                    'account_id': line.account_id.id,
                    'debit': 0.0,
                    'credit': 0.0,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'analytic_account_id': False,
                    'ref': slip.number,
                    'quantity': 1
                }

                #Setting Analysis Account for Salary Slip Lines
                if line.analytic_account_id:
                    rec['analytic_account_id'] = line.analytic_account_id.id
                else:
                    rec['analytic_account_id'] = slip.deg_id.account_id.id

                if line.type == 'allowance' or line.type == 'otherpay':
                    rec['debit'] = amount
                    if not partner.property_account_payable:
                        raise osv.except_osv(_('Configuration Error !'), _('Please Configure Partners Payable Account!!'))
                    ded_rec = {
                        'move_id': move_id,
                        'name': name,
                        'partner_id': partner_id,
                        'date': slip.date,
                        'account_id': partner.property_account_payable.id,
                        'debit': 0.0,
                        'quantity': 1,
                        'credit': amount,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id,
                        'ref': slip.number
                    }
                    line_ids += [movel_pool.create(cr, uid, ded_rec, context=context)]
                elif line.type == 'deduction' or line.type == 'otherdeduct':
                    if not partner.property_account_receivable:
                        raise osv.except_osv(_('Configuration Error !'), _('Please Configure Partners Receivable Account!!'))
                    rec['credit'] = amount
                    total_deduct += amount
                    #selvam linking to tds entires                
                    if line.category_id.tds:
                        tds =  self.pool.get("account.tds")
                        tds_line =  self.pool.get("account.tds.line")
                        g_ids = self.pool.get('res.partner').search(cr,uid,[('name','=','GOVT')])
                        if not g_ids:
                            osv.raise_osv('Govt','You need to have GOVT partner for enconding TDS deduction')
                        """
                        nature_ids = self.pool.get('account.tds.nature').search(cr,uid,[('name','=','Salary')])
                        if not nature_ids:
                            osv.raise_osv('Nature of payment','You need to have a nature of payment called: "Salary"')
                        """
                        tds_line=[{'tds_tax':'ic','rate':line.amount,'debit':0.0,'credit':amount,'base':value}]
                        tds_line_id = tds_line.create(cr,uid,tds_line)
                        tds_id = tds.create(cr,uid,{'date':slip.date,'inv_line_id':line.id,'name':'TDS from salary',
                                            'tds_nature_id':line.category_id.tds_nature_id.id,'tds_acc_id': line.account_id.id,'amount':value,
                                            'tds_amount':amount,'tds_payable':(value-amount),                                        
                                            'tds_line_id':[(6,0,[tds_line_id])],'type':'cr','paid':False,'state':'confirmed','zero':False,
                                            'partner_id':partner_id,'invoice_partner_id':partner_ids                                            
                                            
                                            })
                    ded_rec = {
                        'move_id': move_id,
                        'name': name,
                        'partner_id': partner_id,
                        'date': slip.date,
                        'quantity': 1,
                        'account_id': partner.property_account_receivable.id,
                        'debit': amount,
                        'credit': 0.0,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id,
                        'ref': slip.number
                    }
                    if line.category_id.tds:
                        ded_rec.update({'tds_id':tds_id})
                    ml_id =movel_pool.create(cr, uid, ded_rec, context=context)                                            
                    line_ids += [ml_id]


                line_ids += [movel_pool.create(cr, uid, rec, context=context)]

                # if self._debug:
                #    for contrib in line.category_id.contribute_ids:
                #       _log.debug("%s %s %s %s %s",  contrib.name, contrub.code, contrub.amount_type, contrib.contribute_per, line.total)

            adj_move_id = False
            if total_deduct > 0:
                move = {
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'date': slip.date,
                    'ref':slip.number,
                    'narration': 'Adjustment: %s' % (slip.name)
                }
                adj_move_id = move_pool.create(cr, uid, move, context=context)
                name = "Adjustment Entry - %s" % (slip.employee_id.name)
                self.create_voucher(cr, uid, [slip.id], name, adj_move_id)

                ded_rec = {
                    'move_id': adj_move_id,
                    'name': name,
                    'partner_id': partner_id,
                    'date': slip.date,
                    'account_id': partner.property_account_receivable.id,
                    'debit': 0.0,
                    'quantity': 1,
                    'credit': total_deduct,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'ref': slip.number
                }
                line_ids += [movel_pool.create(cr, uid, ded_rec, context=context)]
                cre_rec = {
                    'move_id': adj_move_id,
                    'name': name,
                    'partner_id': partner_id,
                    'date': slip.date,
                    'account_id': partner.property_account_payable.id,
                    'debit': total_deduct,
                    'quantity': 1,
                    'credit': 0.0,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'ref': slip.number
                }
                line_ids += [movel_pool.create(cr, uid, cre_rec, context=context)]

            rec = {
                'state':'confirm',
                'move_line_ids':[(6, 0,line_ids)],
            }
            if not slip.period_id:
                rec['period_id'] = period_id

            dates = prev_bounds(slip.date)
            exp_ids = exp_pool.search(cr, uid, [('date_valid','>=',dates[0]), ('date_valid','<=',dates[1]), ('state','=','invoiced')], context=context)
            """selvam removed following expense part
            if exp_ids:
                acc = property_pool.get(cr, uid, 'property_account_expense_categ', 'product.category')
                for exp in exp_pool.browse(cr, uid, exp_ids, context=context):
                    exp_res = {
                        'name':exp.name,
                        'amount_type':'fix',
                        'type':'otherpay',
                        'category_id':exp.category_id.id,
                        'amount':exp.amount,
                        'slip_id':slip.id,
                        'expanse_id':exp.id,
                        'account_id':acc
                    }
                    payslip_pool.create(cr, uid, exp_res, context=context)
            """
            """selvam starts """
            register_pool = self.pool.get('company.contribution')
            register_line_pool = self.pool.get('hr.contibution.register.line')
            base = {
                'basic':slip.basic,
                'net':slip.net,
                'gross':slip.grows,
            }            
            print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx"
            for line in slip.line_ids:
                base[line.code.lower()] = line.total
                for contrib in line.category_id.contribute_ids:
                    print "In contirb",contrib.register_id
                    if contrib.register_id:
                        value = eval(line.category_id.base, base)
                        company_contrib = register_pool.compute(cr, uid, contrib.id, value, context)
                        reg_line = {
                            'name':line.name,
                            'register_id': contrib.register_id.id,
                            'code':line.code,
                            'employee_id':slip.employee_id.id,
                            'emp_deduction':line.total,
                            'comp_deduction':company_contrib,
                            'total':line.total + line.total
                        }
                        print "Creating reg line",contrib.register_id.account_id
                    
                        register_line_pool.create(cr, uid, reg_line)
                        #Selvam - Post contibution into respective Payable and expense accounts
                        ded_rec = {
                        'move_id': move_id,
                        'name': name,
                        'partner_id': partner_id,
                        'date': slip.date,
                        'account_id': contrib.register_id.account_id.id,
                        'debit': company_contrib,
                        'quantity': 1,
                        'credit':0.0 ,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id,
                        'ref': slip.number
                        }
                        print ded_rec,"+++++++++++++++"
                        line_ids += [movel_pool.create(cr, uid, ded_rec, context=context)]
                        g_ids = self.pool.get('res.partner').search(cr,uid,[('name','=','GOVT')])
                        if not g_ids:
                            osv.raise_osv('Govt','You need to have GOVT partner for enconding employer contribution')

                        ded_rec = {
                        'move_id': move_id,
                        'name': name,
                        'partner_id': g_ids[0],
                        'date': slip.date,
                        'account_id': line.account_id.id,
                        'debit': 0.0,
                        'quantity': 1,
                        'credit':company_contrib,
                        'journal_id': slip.journal_id.id,
                        'period_id': period_id,
                        'ref': slip.number
                        }
                        curr_ml_id = movel_pool.create(cr, uid, ded_rec, context=context)
                        
                        line_ids += [curr_ml_id]

            """selvam ends """
            self.write(cr, uid, [slip.id], rec, context=context)

        return True
hr_payslip()
