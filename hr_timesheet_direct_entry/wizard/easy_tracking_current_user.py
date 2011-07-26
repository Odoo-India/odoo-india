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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import osv, fields
from tools.translate import _

class easy_tracking_currenct_user(osv.osv_memory):
    _name = 'easy.tracking.current.user'
    _description = 'easy.tracking.current.user'
    _columns = {
        'user_id': fields.many2one('res.users', 'User'),
        'timesheet_date': fields.date('Timesheet Date')
    }

    def default_get(self, cr, uid, fields, context=None):
        res = super(easy_tracking_currenct_user, self).default_get(cr, uid, fields, context=context)
        user_pool = self.pool.get('res.users')
        current_user = user_pool.browse(cr, uid, uid, context=context)
        res['user_id'] = current_user.id
        res['timesheet_date'] = time.strftime("%Y-%m-%d")
        return res

    def create_tracking_line_entry(self, cr, uid, tracking_id, from_date, to_date, context=None):
        if context is None:
            context = {}

        project_obj = self.pool.get('project.project')
        tracking_obj = self.pool.get('easy.tracking')
        tracking_line_obj = self.pool.get('easy.tracking.line')
        timesheet_analytic_obj = self.pool.get('hr.analytic.timesheet')

        project_ids = project_obj.search(cr, uid, [])

        track_data = tracking_obj.browse(cr, uid, tracking_id, context=context)
        for track_line in track_data.tracking_line_ids:
            tracking_line_obj.write(cr, uid, [track_line.id],{'monday':0.0,
                                                              'tuesday':0.0,
                                                              'wednesday':0.0,
                                                              'thursday':0.0,
                                                              'friday':0.0,
                                                              'saturday':0.0,
                                                              'sunday':0.0},context=context)

        for project in project_obj.browse(cr, uid, project_ids, context=context):

            context.update({'project_id':project.id})

            timesheet_analytic_ids = timesheet_analytic_obj.search(cr, uid, [('account_id','=',project.analytic_account_id.id),('user_id','=',uid),('date','>=',from_date),('date','<=',to_date)])

            for analytic_line in timesheet_analytic_obj.browse(cr, uid, timesheet_analytic_ids, context=context):
                entry_date = datetime.strptime(analytic_line.date, '%Y-%m-%d')
                analytic_line_day = entry_date.strftime('%A')

                tracking_line_id = tracking_line_obj.search(cr, uid, [('project_id','=',project.id),('tracking_id','=',tracking_id)])
                if not tracking_line_id:
                    tracking_line_id = tracking_line_obj.create(cr, uid, {'tracking_id':tracking_id, 'project_id':project.id})

                if isinstance(tracking_line_id, int):
                    tracking_line_id = [tracking_line_id]

                if analytic_line_day == 'Monday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'monday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Tuesday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'tuesday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Wednesday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'wednesday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Thursday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'thursday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Friday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'friday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Saturday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'saturday':analytic_line.unit_amount},context=context)
                if analytic_line_day == 'Sunday':
                    tracking_line_obj.write(cr, uid, tracking_line_id, {'sunday':analytic_line.unit_amount},context=context)

        return True

    def check_member_project(self, cr, uid, tracking_id, context=None):
        if context is None:
            context = {}

        tracking_line_obj = self.pool.get('easy.tracking.line')
        project_obj = self.pool.get('project.project')
        project_ids = project_obj.search(cr, uid, [])

        for project in project_obj.browse(cr, uid, project_ids, context=context):
            for member in project.members:
                if member.id == uid:
                    tracking_line_id = tracking_line_obj.search(cr, uid, [('tracking_id','=',tracking_id), ('project_id','=',project.id)])
                    if tracking_line_id:
                        continue
                    tracking_line_obj.create(cr, uid, {'tracking_id':tracking_id, 'project_id':project.id})
        return True

    def open_tracking(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        tracking_obj = self.pool.get('easy.tracking')
        tracking_line_obj = self.pool.get('easy.tracking.line')
        timesheet_analytic_obj = self.pool.get('hr.analytic.timesheet')

        data = self.read(cr, uid, ids)[0]
        sheet_date = data['timesheet_date']
        user_id = data['user_id']

        context.update({'sheet_date':sheet_date, 'user_id':user_id})
        sheet_current_week_from_day = datetime.strptime(sheet_date, '%Y-%m-%d').strftime('%A')
        if sheet_current_week_from_day == 'Monday':
            sheet_current_week_from = datetime.strptime(sheet_date,'%Y-%m-%d') + relativedelta(days=0)
        else:
            sheet_current_week_from = datetime.strptime(sheet_date,'%Y-%m-%d') + relativedelta(weekday=0, weeks=-1)
        sheet_currenct_week_to = datetime.strptime(sheet_date,'%Y-%m-%d') + relativedelta(weekday=6)

        employee_ids = self.pool.get('hr.employee').search(cr, uid, [('user_id','=',user_id)], context=context) # search employee for this user
        if not len(employee_ids):
            raise osv.except_osv(_('Error !'), _('No employee defined for your user !'))

        tracking_ids = tracking_obj.search(cr, uid, [('employee_id','=',employee_ids[0])], context=context)

        if tracking_ids:
            self.create_tracking_line_entry(cr, user_id, tracking_ids[0], sheet_current_week_from, sheet_currenct_week_to, context=context)
            self.check_member_project(cr, uid, tracking_ids[0], context=context)
            domain = "[('id','=',%s),('user_id', '=', uid)]" % (tracking_ids[0],)
        else:
            tracking_id = tracking_obj.create(cr, uid, {'employee_ids':employee_ids[0]})
            self.create_tracking_line_entry(cr, user_id, tracking_id, sheet_current_week_from, sheet_currenct_week_to, context=context)
            self.check_member_project(cr, uid, tracking_id, context=context)
            domain = "[('id','=',%s),('user_id', '=', uid)]" % (tracking_id,)

        value = {
            'domain': domain,
            'name': _('My Easy Tracking'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'easy.tracking',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
        }

        if tracking_ids:
            value['res_id'] = tracking_ids[0]
        else:
            value['res_id'] = tracking_id

        return value

easy_tracking_currenct_user()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
