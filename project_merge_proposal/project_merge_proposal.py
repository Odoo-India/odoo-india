# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields
import datetime
import time
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

WORK_STATE = [('draft', 'New'), ('open', 'In Progress'), ('needs_review', 'Needs review'), ('code_failed', 'Code failed to merge'), ('pending', 'Pending'),('in_reviewing','Review in progress'), ('ready', 'Approved'), ('done', 'Done'), ('cancelled', 'Cancelled'), ('rejected', 'Rejected')]

REVIEW_STATE = [('resubmit', 'Resubmit'), ('none','No Comments'),
                   ('approved', 'Approve'),
                   ('need_fixing', 'Needs Fixing'),
                   ('need_information', 'Needs Information'),
                   ('disapproved', 'Disapprove')
             ]

class project_work_review(osv.osv):
    _name = "project.task.work.review"
    _columns = {
        'ref_id': fields.integer('Ref. Id'),
        'name': fields.char('Review summary', size=128),
        'date': fields.datetime('Date', select="1"),
        'work_id': fields.many2one('project.task.work', 'Work', ondelete='cascade', required=True, select="1"),
        'hours': fields.float('Time Spent'),
        'user_id': fields.many2one('res.users', 'Review by'),
        'company_id': fields.related('work_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'user_name': fields.char('Reviewer', size=128, help="Launchpad Login of Reviewer"),
        'description': fields.text('Description'),
        'state': fields.selection(REVIEW_STATE, 'State', required=True),
    }
    _defaults = {
        'state': 'none',
        'user_id': lambda obj, cr, uid, context: uid,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'project.task', context=c)
    }
project_work_review()

class project_merge_proposal(osv.osv):
    _inherit = "project.task.work"
    def _compute(self, cr, uid, ids, fields, arg, context=None):
        res = {}
        resource_calendar = self.pool.get('resource.calendar')
        resource_calendar_id = False
        for work in self.browse(cr, uid, ids, context=context):
            approved = 0.000
            need_fixing = 0.000
            resubmit = 0.000
            hours = 0.0
            if 'hours' in fields and work.date_started and work.date:
                date_started = datetime.datetime.strptime(work.date_started, DEFAULT_SERVER_DATETIME_FORMAT)
                date = datetime.datetime.strptime(work.date, DEFAULT_SERVER_DATETIME_FORMAT)
                resource_calendar_id = (work.task_id and work.task_id.project_id) and work.task_id.project_id.resource_calendar_id or False
                if resource_calendar_id:
                    hours = resource_calendar.interval_hours_get(cr, uid, resource_calendar_id.id, date_started, date, resource=work.user_id and work.user_id.id or False)
                else:
                    hours = (time.mktime(date.timetuple()) - time.mktime(date_started.timetuple()))/3600
            for review in work.review_ids:
                if review.state == 'approved': approved += 1.000
                if review.state == 'need_fixing': need_fixing += 1.000
                if review.state == 'resubmit': resubmit += 1.000
            res[work.id] = {
                'approve_ratio': len(work.review_ids) and approved/len(work.review_ids) or 0.000,
                'need_fixing_ratio': len(work.review_ids) and need_fixing/len(work.review_ids) or 0.000,
                'resubmit_ratio': len(work.review_ids) and resubmit/len(work.review_ids) or 0.000,
                'hours': hours
            }
        return res
    _columns = {
                'review_ids': fields.one2many('project.task.work.review', 'work_id', 'Reviews'),
                'task_id': fields.many2one('project.task', 'Task'),
                'date_started': fields.datetime('Started Date'),
                'date_done': fields.datetime('Done Date', help="Date of Merged"),
                'date': fields.datetime('Submitted Date'),
                'source_branch_link': fields.char('Source Branch', size=512),
                'target_branch_link': fields.char('Target Branch', size=512),
                'state': fields.selection(WORK_STATE, 'State', required=True),
                'description': fields.text('Description'),
                'user_name': fields.char('Submitter',size=128, help="Launchpad Login of Submitter"),
                'reporter_name': fields.char('Merger Reporter',size=128),
                'reporter_user_id': fields.many2one('res.users', 'Merger Reporter', help="Launchpad Login of Merger"),
                'user_id': fields.many2one('res.users', 'Submitted by'),
                'diff_new_lines': fields.integer('Diff. New Lines'),
                'diff_rem_lines': fields.integer('Diff. Remove Lines'),
                'diff_modification_files': fields.integer('Diff. Modification Files'),
                'diff_modification_lines': fields.integer('Diff. Modification Lines'),
                'approve_ratio': fields.function(_compute, string='Ratio of Approved', multi='approve_ratio', help="Ratio = No. of Approved Review / Total Reviews"),
                'need_fixing_ratio': fields.function(_compute, string='Ratio of Need Fixing', multi='need_fixing_ratio', help="Ratio = No. of Need Fixing Review / Total Reviews"),
                'resubmit_ratio': fields.function(_compute, string='Ratio of Resubmit', multi='resubmit_ratio', help="Ratio = No. of ReSubmit / Total Reviews"),
                #'hours': fields.function(_compute, string='Time Spent', multi='hours', help="Hours = Start Date - Submmitted Date"),
    }
    _defaults = {
        'state': 'draft',
    }

project_merge_proposal()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
