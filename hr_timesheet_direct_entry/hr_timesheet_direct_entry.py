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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tools.translate import _

class easy_tracking(osv.osv):
    _name = "easy.tracking"
    _description = "Easy Tracking"
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True),
        'tracking_line_ids': fields.one2many('easy.tracking.line', 'tracking_id', 'Tracking Lines')
    }

    def _default_employee(self,cr, uid, context=None):
        emp_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',uid)], context=context)
        return emp_ids and emp_ids[0] or False

    _defaults = {
        'employee_id': _default_employee,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(easy_tracking, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if context.get('sheet_date', False):
            current_date = context['sheet_date']
            current_week_from_day = datetime.strptime(current_date, '%Y-%m-%d').strftime('%A')
            if current_week_from_day == 'Monday':
                current_week_from = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=0) # start date of week
            else:
                current_week_from = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=0, weeks=-1) # start date of week
            currenct_week_to = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=6) # end date of week
            if 'tracking_line_ids' in res['fields']:
                tracking_line_fields = res['fields']['tracking_line_ids']['views']['tree']['fields']
                for field in tracking_line_fields:
                    if field == 'monday':
                        new_date = current_week_from + relativedelta(days=0)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['monday']['string'] = 'Mon' + "(%s)"%label
                    if field == 'tuesday':
                        new_date = current_week_from + relativedelta(days=1)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['tuesday']['string'] = 'Tus' + "(%s)"%label
                    if field == 'wednesday':
                        new_date = current_week_from + relativedelta(days=2)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['wednesday']['string'] = 'Wed' + "(%s)"%label
                    if field == 'thursday':
                        new_date = current_week_from + relativedelta(days=3)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['thursday']['string'] = 'Thu' + "(%s)"%label
                    if field == 'friday':
                        new_date = current_week_from + relativedelta(days=4)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['friday']['string'] = 'Fri' + "(%s)"%label
                    if field == 'saturday':
                        new_date = current_week_from + relativedelta(days=5)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['saturday']['string'] = 'Sat' + "(%s)"%label
                    if field == 'sunday':
                        new_date = current_week_from + relativedelta(days=6)
                        label = new_date.strftime('%d') + new_date.strftime('%B')
                        tracking_line_fields['sunday']['string'] = 'Sun' + "(%s)"%label
        return res

easy_tracking()

class easy_tracking_line(osv.osv):
    _name = "easy.tracking.line"
    _description = "Easy Tracking Line"
    _columns = {
        'project_id': fields.many2one('project.project', 'Project', required=True, select=True),
        'tracking_id': fields.many2one('easy.tracking', 'Tracking'),
        'sunday': fields.float('Sunday'),
        'monday': fields.float('Monday'),
        'tuesday': fields.float('Tuesday'),
        'wednesday': fields.float('Wednesday'),
        'thursday': fields.float('Thursday'),
        'friday': fields.float('Friday'),
        'saturday': fields.float('Saturday'),
    }

    def create_anayltic_line(self, cr, uid, data_line, context=None):
        if context is None:
            context = {}
        timesheet_analytic_obj = self.pool.get('hr.analytic.timesheet')
        timesheet_line_id = timesheet_analytic_obj.create(cr, uid, data_line)
        return timesheet_line_id

    def write_line(self, cr, uid, project_id, amount, day, context=None):
        if context is None:
            context = {}

        imp_value = {}
        timesheet_obj = self.pool.get('hr_timesheet_sheet.sheet')
        timesheet_analytic_obj = self.pool.get('hr.analytic.timesheet')
        project_obj = self.pool.get('project.project')
        uom_obj = self.pool.get('product.uom')
        emp_obj = self.pool.get('hr.employee')

        emp_id = emp_obj.search(cr, uid, [('user_id', '=', uid)]) # Find employee for user
        emp = emp_obj.browse(cr, uid, emp_id[0])

        if context.get('sheet_date', False):
            current_date = context['sheet_date']
            current_week_from_day = datetime.strptime(current_date, '%Y-%m-%d').strftime('%A')
            if current_week_from_day == 'Monday':
                current_week_from = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=0) # start date of week
            else:
                current_week_from = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=0, weeks=-1) # start date of week
            currenct_week_to = datetime.strptime(current_date,'%Y-%m-%d') + relativedelta(weekday=6) # end date of week

            project_data = project_obj.browse(cr, uid, project_id)
            if not emp.product_id:
                raise osv.except_osv(_('Bad Configuration !'),
                     _('No product defined on the related employee.\nFill in the timesheet tab of the employee form.'))
            if not emp.journal_id:
                raise osv.except_osv(_('Bad Configuration !'),
                     _('No journal defined on the related employee.\nFill in the timesheet tab of the employee form.'))
            general_account_id = emp.product_id.product_tmpl_id.property_account_expense.id
            if not general_account_id:
                general_account_id = emp.product_id.categ_id.property_account_expense_categ.id
                if not general_account_id:
                    raise osv.except_osv(_('Bad Configuration !'),
                            _('No product and product category property account defined on the related employee.\nFill in the timesheet tab of the employee form.'))

            analytic_account_id = project_data.analytic_account_id.id or False
            if not analytic_account_id:
                raise osv.except_osv(_('Bad Configuration !'),
                        _('No Analytic account defined on the related project.'))

            enter_date = current_week_from + relativedelta(days=day)
            data_line = {
                        'name' :'Work',
                        'date': enter_date,
                        'account_id':analytic_account_id,
                        'general_account_id':general_account_id,
                        'journal_id':emp.journal_id.id,
                        'product_id':emp.product_id.id,
                        'product_uom_id':emp.product_id.uom_id.id,
                       }
            timesheet_line_id = timesheet_analytic_obj.search(cr, uid, [('date','=',enter_date),('account_id','=',analytic_account_id)])
            if not timesheet_line_id:
                timesheet_line_id = self.create_anayltic_line(cr, uid, data_line)

            default_uom = self.pool.get('res.users').browse(cr, uid, uid).company_id.project_time_mode_id.id # Find default unit of user company
            if emp.product_id.uom_id.id != default_uom:
                imp_value['unit_amount'] = uom_obj._compute_qty(cr, uid, default_uom, amount, emp.product_id.uom_id.id) # Calculate unit amount if different then company unit
            else:
                imp_value['unit_amount'] = amount

            amount_unit = timesheet_analytic_obj.on_change_unit_amount(cr, uid, timesheet_line_id, emp.product_id.id,  amount,  False, False, data_line['journal_id'])
            if amount_unit and 'amount' in amount_unit.get('value',{}):
                imp_value.update({'amount': amount_unit['value']['amount'] })
                if timesheet_line_id and isinstance(timesheet_line_id, (int, long)):
                    timesheet_line_id = [timesheet_line_id]
            timesheet_analytic_obj.write(cr, uid, timesheet_line_id, imp_value)
        return True

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if 'monday' in vals and vals['monday']:
             self.write_line(cr, uid, vals['project_id'], vals['monday'], 0, context=context)
        if 'tuesday' in vals and vals['tuesday']:
            self.write_line(cr, uid, vals['project_id'], vals['tuesday'], 1, context=context)
        if 'wednesday' in vals and vals['wednesday']:
            self.write_line(cr, uid, vals['project_id'], vals['wednesday'], 2, context=context)
        if 'thursday' in vals and vals['thursday']:
            self.write_line(cr, uid, vals['project_id'], vals['thursday'], 3, context=context)
        if 'friday' in vals and vals['friday']:
            self.write_line(cr, uid, vals['project_id'], vals['friday'], 4, context=context)
        if 'saturday' in vals and vals['saturday']:
            self.write_line(cr, uid, vals['project_id'], vals['saturday'], 5, context=context)
        if 'sunday' in vals and vals['sunday']:
            self.write_line(cr, uid, vals['project_id'], vals['sunday'], 6, context=context)
        return super(easy_tracking_line,self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        if 'project_id' in vals:
            project_id = vals['project_id']
        else:
            project_id = context.get('project_id',False)

        if 'monday' in vals and vals['monday']:
             self.write_line(cr, uid, project_id, vals['monday'], 0, context=context)
        if 'tuesday' in vals and vals['tuesday']:
            self.write_line(cr, uid, project_id, vals['tuesday'], 1, context=context)
        if 'wednesday' in vals and vals['wednesday']:
            self.write_line(cr, uid, project_id, vals['wednesday'], 2, context=context)
        if 'thursday' in vals and vals['thursday']:
            self.write_line(cr, uid, project_id, vals['thursday'], 3, context=context)
        if 'friday' in vals and vals['friday']:
            self.write_line(cr, uid, project_id, vals['friday'], 4, context=context)
        if 'saturday' in vals and vals['saturday']:
            self.write_line(cr, uid, project_id, vals['saturday'], 5, context=context)
        if 'sunday' in vals and vals['sunday']:
            self.write_line(cr, uid, project_id, vals['sunday'], 6, context=context)

        return super(easy_tracking_line,self).write(cr, uid, ids, vals, context=context)

easy_tracking_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
