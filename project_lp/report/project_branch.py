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

import datetime, time
from report import report_sxw
from operator import itemgetter

class project_branch(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(project_branch, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_project': self.get_project,
            'get_project_data': self.get_project_data,
        })

    def date_format(self,date_time):
        days = ''
        mins = ''
        hours = ''
        sec=''
        if not date_time.days:
            date_lst = str(date_time).split(':')
        else:
            date_lst = str(date_time).split(',')[1]
            date_lst = date_lst.split(':')

        if int(date_time.days) != 0:
            days = str(date_time.days)+'d'

        if int(date_lst[0]) != 0:
            hours = date_lst[0]+'h'
        if int(date_lst[1]) !=0:
            mins = date_lst[1]+'m'
        if float(date_lst[2]) !=0.0:
            sec = str(date_lst[2]).split('.')[0]+'s'

        string_date = days+' '+hours+' '+mins+' '+sec
        return string_date

    def get_project(self, data):
        result = {}
        if data.get('form', False) and data['form'].get('project_id', False):
            result['project_name'] = data['form'].get('project_id', False)[1]
            state_list = ['Development', 'Abandoned', 'Experimental', 'Mature', 'Merged']
            selected_list = []
            for state in state_list:
                if data['form'][state]:
                    selected_list.append(state)
            result['state'] = selected_list

            result['date_start'] = data['form'].get('date_start', False)
            result['date_end'] = data['form'].get('date_end', False)
            project_id = data['form'].get('project_id', False)[0]
            if project_id:
                self.cr.execute('select min(pbm.date_created-pb.date_created) as day_min, max(pbm.date_created-pb.date_created) as day_max'
                                ' from project_branch pb '
                                ' left join project_branch_merge pbm on (pbm.branch_id = pb.id)'
                                ' where  pb.project_id = %s and pb.state= %s  and pb.date_created >=%s and pb.date_created <= %s', (str(project_id), 'Merged', result['date_start'], result['date_end']))
                res = self.cr.dictfetchone()

            result['day_min'] = self.date_format(res['day_min'])
            result['day_max'] = self.date_format(res['day_max'])
            result['avg'] = self.date_format((res['day_min'] + res['day_max'])/2)
        return result

    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""
        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        date_from = date_from.split('.')[0]
        date_to = date_to.split('.')[0]
        from_dt = datetime.datetime.strptime(date_from, DATETIME_FORMAT)
        to_dt = datetime.datetime.strptime(date_to, DATETIME_FORMAT)
        timedelta = to_dt - from_dt
        days = ''
        hours = ''
        if timedelta.days != 0:
            days = str(timedelta.days)+'d'
        if timedelta.seconds/60/60 != 0:
            hours =str(timedelta.seconds/60/60)+'h'
        diff_date = days+' '+hours+' '+str(timedelta).split(':')[1]+'m'
        return diff_date

    def get_project_data(self, form):
        res = {}
        result =[]
        exist_state = []
        exist_type = []
        obj_branch = self.pool.get("project.branch")
        project_id = form['project_id'][0]
        btype = {None: '', 'junk': 'Need Review', 'fix': 'Bug Fix', 'not_clean': 'Junk', 'feature': 'Feature', 'improvement': 'Improvements', 'removed': 'Deleted'}
        state_list = ['Development', 'Abandoned', 'Experimental', 'Mature', 'Merged']
        selected_list = []
        dt_start = form['date_start'] or ''
        dt_end = form['date_end'] or ''
        for state in state_list:
            if form[state]:
                selected_list.append(state)
        if not selected_list or not project_id:
            return result
        self.cr.execute('select a.name as project_name,pp.id as project_id, pb.branch_type as type,pb.date_created as pdate_created, pbm.date_created as mdate_created, pb.state,pb.name as branch, pbm.web_link as target_branch'
                        ' from project_branch pb '
                        ' left join project_branch_merge pbm on (pbm.branch_id = pb.id)'
                        ' left join project_project pp on (pp.id = pb.project_id)'
                        ' left join account_analytic_account a on (pp.analytic_account_id = a.id)'
                        ' where pb.state IN %s and pb.project_id = (%s) and pb.date_created >=%s and pb.date_created <= %s and pb.active = True' , (tuple(selected_list), str(project_id), dt_start, dt_end))

        res = self.cr.dictfetchall()
        sorted_data = sorted(res, key=itemgetter('type','state'))

        for data in sorted_data:
            project_name = data['project_name']
            if data['type'] not in exist_type:
                new_dict_type = {}
                exist_state = []

                new_dict_type.update({'type': btype[data['type']] or '' +'('+str(len(obj_branch.search(self.cr, self.uid, [('project_id','=',data['project_id']),('branch_type','=',data['type']),('date_created','>=',dt_start),('date_created','<=',dt_end)])))+')'})
                exist_type.append(data['type'])
                type_branch = data['type']
                result.append(new_dict_type)
                data.update({'type':''})

            data.update({'type':''})
            new_dict_state = {}
            if data['state'] not in exist_state:
                new_dict_state.update({'state': data['state']+'('+str(len(obj_branch.search(self.cr, self.uid, [('project_id','=',data['project_id']),('branch_type','=',type_branch),('state','=',data['state']),('date_created','>=',dt_start),('date_created','<=',dt_end)])))+')'})
                exist_state.append(data['state'])
                result.append(new_dict_state)
                data.update({'state':''})

            data.update({'state':''})
            if data['mdate_created']:
                data['delay'] = self._get_number_of_days(data['pdate_created'], data['mdate_created'])

            if not data['target_branch']:
                data['target_branch'] = ''
            data.update({'target_branch':str(data['target_branch']).split(project_name)[-1]})
            result.append(data)
        return result

report_sxw.report_sxw('report.project.branch', 'project.branch', 'addons/project_lp/report/project_branch.rml', parser=project_branch, header="internal")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: