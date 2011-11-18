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

from osv import osv

from launchpadlib.launchpad import Launchpad, EDGE_SERVICE_ROOT
from datetime import datetime, date
from bzrlib.branch import Branch
import os

MERGE_STATUS = {}
MERGE_STATUS_FILTERS = ['rejected', 'pending', 'cancelled', 'done']
MERGE_STATUS.update({'Rejected':'rejected' , 'Queued': 'pending', 'Superseded':'cancelled', 'Merged':'done' })
MERGE_STATUS.update({'Needs review': 'needs_review', 'Code failed to merge':'code_failed', 'Work in progress':'in_reviewing', 'Approved': 'ready' })

BRANCH_STATUS = {}
BRANCH_STATUS.update({'Merged':'merged', 'Abandoned':'cancelled'})
BRANCH_STATUS.update({'Experimental':'experimental', 'Development': 'development', 'Mature':'mature'})

COMMENT_STATUS = { 'Resubmit':'resubmit',
                   'Approve': 'approved',
                   'Needs Fixing': 'need_fixing',
                   'Needs Information': 'need_information',
                   'Disapprove': 'disapproved' }
DEFAULT_LOGIN = 'hmo-tinyerp'
DEFAULT_CACHE_PATH = "~/.launchpadlib/cache"

TEAMS = ['openerp', 'openerp-dev'] #,'openobject-training', 'openerp-opw']
PROJECTS = ['openerp', 'openobject-addons', 'openobject-client', 'openerp-web', 'openobject-server','openobject-client-web']

LP_API_LINK = "https://api.edge.launchpad.net/1.0/"
def get_lp():
    cachedir = os.path.expanduser(DEFAULT_CACHE_PATH)
    return Launchpad.login_with(DEFAULT_LOGIN, EDGE_SERVICE_ROOT, cachedir)

class project_launchpad_scheduler(osv.osv_memory):
    _name = "project.launchpad.scheduler"
    launchpad = None

    def get_email_address(self, people):
        return [email_address.email for email_address in people.confirmed_email_addresses]

    def lp_load_link(self, link):
        if self.launchpad is None:
            self.launchpad = get_lp()
        res = False
        try:
            res = self.launchpad.load(link)
        except Exception, e:
            print e
        return res

    def get_lp_people(self, people):
        if self.launchpad is None:
            self.launchpad = get_lp()
        return self.launchpad.people[people]

    def get_lp_project(self, project):
        if project is None or not project or project == 'none':
            return False
        if self.launchpad is None:
            self.launchpad = get_lp()
        return self.launchpad.projects[project]

    def get_lp_people_by_email(self, email):
        if self.launchpad is None:
            self.launchpad = get_lp()
        return self.launchpad.people.getByEmail(email=email)

    def get_lp_branches(self, people):
        return people.getBranches(status=BRANCH_STATUS.keys())

    def _lp_merge_proposal(self, proposal, from_date=False):
        merge_request = {}
        if proposal is None:
            return merge_request
        proposal_date = proposal.date_created
        
        if from_date and datetime(proposal_date.year, proposal_date.month, proposal_date.day) <= datetime(from_date.year, from_date.month, from_date.day):
            return merge_request
        
        merge_request['date_created'] = proposal_date
        merge_request['date_merged'] = proposal.date_merged
        preview_diff = proposal.preview_diff #_link and self.load_link(proposal.preview_diff_link) or None

        merge_request['added_lines_count'] = preview_diff and preview_diff.added_lines_count or 0
        merge_request['remove_lines_count'] = preview_diff and preview_diff.removed_lines_count or 0
        merge_request['diff_lines_count'] = preview_diff and preview_diff.diff_lines_count or 0
        merge_request['diffstat'] = preview_diff and (preview_diff.diffstat or {}) or {}
        merge_request['diffstat_files_count'] = len(merge_request['diffstat'].keys())
        merge_request['description'] = proposal.description
        merge_request['state'] = MERGE_STATUS.get(proposal.queue_status)
        merge_request['name'] = proposal.self_link.replace(LP_API_LINK, "")
        merge_request['source_branch_link'] = proposal.source_branch_link.replace(LP_API_LINK, "")
        merge_request['date_created_branch'] = proposal.source_branch.date_created
        merge_request['target_branch_link'] = proposal.target_branch_link.replace(LP_API_LINK, "")
        merge_request['registrant_name'] = proposal.registrant.name
        merge_request['merge_reporter'] =  proposal.merge_reporter and proposal.merge_reporter.name or False
        merge_request['registrant_email_address'] = self.get_email_address(proposal.registrant)

        comments = []
        for review in proposal.all_comments_collection:
            comment = {}
            comment['date'] = review.date_created
            comment['author_name'] = review.author.name
            comment['author_email'] = self.get_email_address(review.author)
            comment['message'] = review.message_body
            comment['title'] = review.title
            comment['id'] = review.id
            comment['vote'] = COMMENT_STATUS.get(review.vote)
            comment['branch'] = proposal.source_branch_link
            comments.append(comment)
        merge_request['comments'] = comments
        return merge_request

    def get_lp_merge_proposal(self, team, from_date=False):
        merge_requests = []
        merge_state = []
        for key, value in MERGE_STATUS.items():
            if value in MERGE_STATUS_FILTERS:
                continue
            merge_state.append(key)

        for proposal in team.getMergeProposals(status=merge_state):
            merge_requests.append(self._lp_merge_proposal(proposal, from_date))
        return merge_requests

    def get_revisions(self, branch_name, location, from_date=False):
        branch = Branch.open_containing(location)[0]

        #last_revision = branch.revno() - 100
        revisions = branch.revision_history()
        commits = []
        for revision in revisions:
            rev_id = branch.repository.get_revision(revision)
            commit_time = rev_id.timestamp
            commit_date = date.fromtimestamp(commit_time)
            if from_date and datetime(commit_date.year, commit_date.month, commit_date.day) <= datetime(from_date.year, from_date.month, from_date.day):
                continue
            commit = {}
            commit['date'] = commit_date
            rev_no = branch.revision_id_to_revno(rev_id)
            commit['rev_id'] = rev_id
            commit['rev_no'] = rev_no
            commit['message'] = revision.get_summary().encode('utf-8')
            commit['author_email'] = revision.get_apparent_author().encode('utf-8')
            commit['ass_bugs'] =[[rev_no,bug] for bug in revision.iter_bugs()]
            commit['branch'] = branch_name
            commits.append(commit)
        return commits

    def get_user_by_launchpad_login(self, cr, uid, launchpad_login):
        if not launchpad_login:
            return False
        res_users = self.pool.get('res.users')
        login = launchpad_login.split('-')
        user_ids = res_users.search(cr, uid, [('login','=',login[0])])
        if user_ids:
            return user_ids[0]
        return False

    def _create_work_review(self, cr, uid, work_id, commits, context=None):
        task_work_review = self.pool.get('project.task.work.review')
        new_ids = []
        for commit in commits:
            user_id = self.get_user_by_launchpad_login(cr, uid, commit['author_name'])
            vals = {
                    'ref_id': commit['id'],
                    'name': commit['title'],
                    'description': commit['message'],
                    'date': commit['date'],
                    'state': commit.get('vote', 'none') or 'none',
                    'user_id': user_id,
                    'user_name': commit['author_name'],
                    'work_id': work_id,
            }
            ids = task_work_review.search(cr, uid, [('ref_id','=', commit['id'])])
            if ids and len(ids):
                task_work_review.write(cr, uid, ids, vals, context=context)
                new_id = ids[0]
            else:
                new_id = task_work_review.create(cr, uid, vals, context=context)
            new_ids.append(new_id)
        return new_ids

    def _create_work(self, cr, uid, merge_proposals,context=None):
        task_work = self.pool.get('project.task.work')
        new_ids = []
        for merge_proposal in merge_proposals:
            user_id = self.get_user_by_launchpad_login(cr, uid, merge_proposal['registrant_name'])
            reporter_user_id = self.get_user_by_launchpad_login(cr, uid, merge_proposal['merge_reporter'])
            vals = {
                     'name':merge_proposal['name'],
                     'date':merge_proposal['date_created'],
                     'date_started': merge_proposal['date_created_branch'],
                     'date_done': merge_proposal['date_merged'],
                     'user_id':user_id,
                     'reporter_user_id': reporter_user_id,
                     'user_name': merge_proposal['registrant_name'],
                     'reporter_name': merge_proposal['merge_reporter'],
                     'description':merge_proposal['description'],
                     'state':merge_proposal['state'],
                     'source_branch_link': merge_proposal['source_branch_link'],
                     'target_branch_link': merge_proposal['target_branch_link'],
                     'diff_new_lines':merge_proposal['added_lines_count'],
                     'diff_rem_lines':merge_proposal['remove_lines_count'],
                     'diff_modification_files':merge_proposal['diffstat_files_count'],
                     'diff_modification_lines':merge_proposal['diff_lines_count']
            }
            ids = task_work.search(cr, uid, [('name','=', merge_proposal['name'])])
            if ids and len(ids):
                task_work.write(cr, uid, ids, vals, context=context)
                new_id = ids[0]
            else:
                new_id = task_work.create(cr, uid, vals, context=context)
            # Take all comments of merge  proposal
            self._create_work_review(cr, uid, new_id, merge_proposal['comments'], context=context)
            new_ids.append(new_id)
        return new_ids

    def update_merge_proposals(self, cr, uid, ids=None, context=None):
        task_work = self.pool.get('project.task.work')
        merge_state = []
        for key, value in MERGE_STATUS.items():
            if value in MERGE_STATUS_FILTERS:
                continue
            merge_state.append(value)
        work_ids = task_work.search(cr, uid, [('state', 'in', merge_state)])
        for work in task_work.browse(cr, uid, work_ids, context=context):
            proposal_link = "%s%s"%(LP_API_LINK, work.name)
            try:
                proposal = self.lp_load_link(proposal_link)
                if proposal:
                    merge_proposals = [self._lp_merge_proposal(proposal)]
                    self._create_work(cr, uid, merge_proposals, context=context)
            except Exception, e:
                print 'Error on Updatation:::', e
        return True

    def process_merge_proposals(self, cr, uid, ids=None, context=None):
        print 'started process...'
        #update details of current merge proposals
        if len(MERGE_STATUS_FILTERS):
            self.update_merge_proposals(cr, uid, ids=ids, context=context)
        
        #take merge new proposals from LP
        for team in TEAMS:
            lp_people = self.get_lp_people(team)
            #take all  merge proposal from lp which is sent by contributors
            try:
                merge_proposals = self.get_lp_merge_proposal(lp_people)
                self._create_work(cr, uid, merge_proposals, context=context)
                cr.commit()
            except Exception, ex:
                print 'ERROR::::', ex
        print 'end process...'
        return True
project_launchpad_scheduler()
