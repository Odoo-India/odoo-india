# -*- encoding: utf-8 -*-
##############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2012 OpenERP s.a. (<http://www.openerp.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import datetime
from bzrlib.branch import Branch
from launchpadlib.launchpad import Launchpad
from launchpadlib.credentials import Credentials

from osv import osv
from osv import fields

CACHE_PATH = "~/.launchpadlib/cache/"

BRANCH_STATUS = [
    ('Experimental','Experimental'),
    ('Development','Development'),
    ('Mature','Mature'),
    ('Merged','Merged'),
    ('Abandoned','Abandoned')
]
MERGE_STATUS = [
    ('Work in progress','Work in progress'),
    ('Needs review','Needs review'),
    ('Approved','Approved'),
    ('Rejected','Rejected'),
    ('Merged','Merged'),
    ('Code failed to merge','Code failed to merge'),
    ('Queued','Queued'),
    ('Superseded','Superseded')
]
REVIEW_STATE = [
    ('Resubmit', 'Resubmit'),
    ('Abstain','Abstain'),
    ('Approve', 'Approve'),
    ('Needs Fixing', 'Needs Fixing'),
    ('Needs Information', 'Needs Information'),
    ('Disapprove', 'Disapprove')
]
BUG_STATUS = [
    ('New','New'),
    ('Incomplete','Incomplete'),
    ('Opinion','Opinion'),
    ('Invalid','Invalid'),
    ('Won\'t Fix','Won\'t Fix'),
    ('Expired','Expired'),
    ('Confirmed','Confirmed'),
    ('Triaged','Triaged'),
    ('In Progress','In Progress'),
    ('Fix Committed','Fix Committed'),
    ('Fix Released','Fix Released')
]
BUG_IMPORTANCE = [
    ('Unknown','Unknown'),
    ('Undecided','Undecided'),
    ('Critical','Critical'),
    ('High','High'),
    ('Medium','Medium'),
    ('Low','Low'),
    ('Wishlist','Wishlist')
]
CODE_LINK = "https://code.launchpad.net/"
BUG_LINK = "https://bugs.launchpad.net/"
LP_API_LINK = "https://api.launchpad.net/1.0/"

_logger = logging.getLogger(__name__)

def get_launchpad():
    credentials = Credentials("OpenERP India")
    credentials.load(file('launchpd-access.txt', 'r'))
    launchpad = Launchpad(credentials, None, None, service_root="production", cache=CACHE_PATH)
    return launchpad

class project_project(osv.osv):
    _inherit = 'project.project'
    _columns = {
        'action_id': fields.many2one('ir.actions.server', 'Email Notification', ondelete='set null', help="Configure email action to get log after each launchpad data process."),
        'log':fields.text('Logs')
    }
project_project()

class res_users(osv.osv):
    _inherit = 'res.users'
    _columns = {
        'lp_user':fields.char('Launchpad User', size=64),
        'lp_email':fields.char('Email Address', size=256)
    }
res_users()

users = {}

def get_user(self, cr, uid, lp_user, context=None):
    user_pool = self.pool.get('res.users')
    global users

    if not context:
        context = {}

    if not users:
        user_ids = user_pool.search(cr, uid, [])
        for user in user_pool.browse(cr, uid, user_ids):
            if user.lp_user:
                users[user.lp_user] = user.id
            else:
                users[user.login] = user.id

    try:
        login = lp_user.name
    except Exception, ex:
        return False
    update = context.get('update',False)
    email = False

    try:
        email = lp_user.confirmed_email_addresses[0].email
    except:
        pass

    if len(login) > 64:
        login = login[0:64]

    user_id = users.get(login, False)
    if not user_id:
        vals = {
            'name':lp_user.display_name,
            'login':login,
            'lp_user':login,
            'password':login,
            'context_lang':'en_US',
            'lp_email':email,
        }
        user_id = user_pool.create(cr, uid, vals, context)
        users[login] = user_id
    elif update:
        vals = {
            'name':lp_user.display_name,
            'lp_email':email,
        }
        user_pool.write(cr, uid, [user_id], vals, context)
    return user_id

class project_branch(osv.osv):
    _name = 'project.branch'
    _description = 'Project Branch'
    _order = 'date_created desc'

    _columns = {
        'name':fields.char('Branch', size=512),
        'user_id':fields.many2one('res.users', 'Owner'),
        'project_id':fields.many2one('project.project', 'Project'),
        'state':fields.selection(BRANCH_STATUS, 'State'),
        'date_created':fields.datetime('Created'),
        'date_last_modified':fields.datetime('Last Modified'),
        'rev_no':fields.integer('Revision'),
        'history':fields.boolean("History ?"),
        'branch_type':fields.selection([('fix','Bug Fix'), ('feature','Feature'), ('improvement','Improvements'), ('junk','Need Review'), ('not_clean','Junk'), ('removed','Deleted')], 'Type'),
        'description':fields.text('Description'),
        'web_link':fields.char('Link', size=2048),
        'branch_format':fields.char('Branch Format', size=2048),
        'repository_format':fields.char('Repository Format', size=2048),
        'control_format':fields.char('Control Format', size=2048),
        'information_type':fields.char('Visibility', size=2048),
        'active':fields.boolean('Active'),
        'branch_ids':fields.one2many('project.branch.merge', 'branch_id', 'Branch'),
        'create_date':fields.datetime('Created on'),
        'write_date':fields.datetime('Updated on'),
    }

    def update_branches(self, cr, uid, ids, context):
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()
        if not ids:
            ids = self.search(cr, uid, [('state','=','Development'), ('rev_no','>',0), ('active','=', True)])
        counter = 0
        _logger.info('%s branches selected to update status' % (len(ids)))
        for branch in self.browse(cr, uid, ids, context):
            counter += 1
            branch_obj = False
            try:
                branch_url = "%s/%s" % (LP_API_LINK, branch.name)
                branch_obj = launchpad.load(branch_url)
            except Exception, ex:
                _logger.error('Branch %s : branch %s seems to removed from Launchpad, De-activated in database !' % (counter, branch_url))
                self.write(cr, uid, [branch.id],{'active':False})
                cr.commit()
                continue

            state = branch_obj.lifecycle_status
            modified_date = branch_obj.date_last_modified
            rev_no = branch_obj.revision_count
            description = branch_obj.whiteboard
            name = branch_obj.unique_name
            branch_type = branch.branch_type

            if rev_no == 0:
                branch_type ='not_clean'
            try:
                if branch_obj.landing_targets:
                    merge = False
                    for proposal in branch_obj.landing_targets:
                        if proposal.queue_status == 'Merged':
                            merge = True
                            break
                    if branch_obj.linked_bugs or 'opw' in name or 'bug' in name or 'fix' in name:
                        branch_type = 'fix'
                    elif merge:
                        branch_type = 'feature'
                elif state == 'Merged':
                    branch_type = 'improvement'
            except:
                pass

            updates = {
                'state':state,
                'date_last_modified':modified_date,
                'rev_no':rev_no,
                'description':description,
                'branch_type':branch_type
            }
            self.write(cr, uid, [branch.id], updates, context)
            _logger.info('Branch %s : Updated branch %s' % (counter, branch_url))

            if counter % 10 == 0:
                cr.commit()
        return True

    def get_launchpad_branches(self, cr, uid, ids, context=None):
        new_branch = []
        new_project = []
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()

        branch_cache = {}

        project_pool = self.pool.get('project.project')
        user_pool = self.pool.get('res.users')
        project_ids = project_pool.search(cr, uid, [('state','=','open')])

        global users

        for oeproject in project_pool.browse(cr, uid, project_ids):
            if oeproject.child_ids:
                continue

            _logger.info('Connection to project %s' % (oeproject.name))
            branches = []
            try:
                project = launchpad.projects[oeproject.name]
                if project:
                    branches = project.getBranches(status = ['Experimental', 'Development', 'Mature', 'Merged', 'Abandoned'])
                    #branches = project.getBranches()
                else:
                    _logger.error('Project not available on Launchpad %s' % (oeproject.name))
                    continue
            except:
                _logger.error('Project not available on Launchpad %s' % (oeproject.name))
                continue

            _logger.info('%s branches selected to process' % (len(branches)))

            ids = self.search(cr, uid, [('project_id','=',oeproject.id)])
            for branch in self.read(cr, uid, ids, ['web_link'], context):
                branch_cache[branch['web_link']] = branch['id']

            new_project.append(oeproject.name)
            counter = 0
            for branch in branches:
                counter += 1
                if branch_cache.get(branch.web_link, 0) > 0:
                    _logger.warning('Branch %s : already exist %s' % (counter, branch))
                    continue

                state = branch.lifecycle_status
                modified_date = branch.date_last_modified
                rev_no = branch.revision_count
                branch_type = 'junk'
                name = branch.unique_name
                description = branch.whiteboard
                branch_format = branch.branch_format
                repository_format = branch.repository_format
                control_format = branch.control_format
                information_type = branch.information_type

                if rev_no == 0:
                    branch_type ='not_clean'
                try:
                    if branch.landing_targets:
                        merge = False
                        for proposal in branch.landing_targets:
                            if proposal.queue_status == 'Merged':
                                merge = True
                                break
                        if branch.linked_bugs or 'opw' in name or 'bug' in name or 'fix' in name:
                            branch_type = 'fix'
                        elif merge:
                            branch_type = 'feature'
                    elif state == 'Merged':
                        branch_type = 'improvement'
                except:
                    pass

                lp_user = branch.registrant
                user_id = False
                if lp_user:
                    user_id = get_user(self, cr, uid, lp_user, context)

                vals = {
                    'name':name,
                    'project_id':oeproject.id,
                    'user_id':user_id,
                    'date_created':branch.date_created,
                    'state':state,
                    'date_last_modified':modified_date,
                    'rev_no':rev_no,
                    'branch_type':branch_type,
                    'description':description,
                    'web_link':branch.web_link,
                    'branch_format':branch_format,
                    'repository_format':repository_format,
                    'control_format':control_format,
                    'information_type':information_type,
                    'active':True
                }
                branch_id = self.create(cr, uid, vals)
                new_branch.append(name)
                _logger.info('Branch %s : imported %s in project %s' % (counter, branch, oeproject.name))
                if counter % 10 == 0:
                    cr.commit()
        if oeproject.action_id:
            message = """Hello !,
We have just processed %(project)s project to get the new branches and we get %(total)s new merge proposals.

List of projects processed :
%(projects)s

Here are the list of new merge proposals :
%(message)s

Regards,
OpenERP Development Team"""
            msg = '\n'.join(str(v) for v in new_branch)
            projects = '\n'.join(str(v) for v in new_project)
            message = message % {'project':len(new_project), 'projects':projects, 'total':str(len(new_branch)), 'message':msg}
            project_pool.write(cr, uid, [oeproject.id], {'log':message})
            cr.commit()
            self.pool.get('ir.actions.server').run(cr, uid, [oeproject.action_id.id], {'active_id':oeproject.id, 'active_ids':[oeproject.id], 'active_model':'project.project'})

        return True
project_branch()

class project_branch_merge_proposal(osv.osv):
    _name = 'project.branch.merge'
    _description = 'Merge Proposal'
    _order = 'date_created desc'

    _columns = {
        'project_id':fields.many2one('project.project', 'Project'),
        'branch_id':fields.many2one('project.branch', 'Branch'),
        'target_branch_id':fields.many2one('project.branch', 'Target Branch'),
        'name':fields.char('Name', size=1024),
        'description':fields.text('Message'),
        'user_id':fields.many2one('res.users', 'Owner'),
        'reviewer_user_id':fields.many2one('res.users', 'Reviewer'),
        'date_created':fields.datetime('Created On'),
        'date_queued':fields.datetime('Requested'),
        'date_reviewed':fields.datetime('Rreviewed On'),
        'rev_no':fields.integer('Revision'),
        'state':fields.selection(MERGE_STATUS, 'State'),
        'web_link':fields.char('Link', size=2048),
        'added_lines_count':fields.integer('Lines Added'),
        'removed_lines_count':fields.integer('Lines Removed'),
        'diff_lines_count':fields.integer('Lines Diff'),
        'diff_file_count':fields.integer('Files Modified'),
        'diff_text':fields.text('Diff'),
        'conflicts':fields.text('Conflicts'),
        'diff_link':fields.char("Diff", size=1024),
        'comment_ids':fields.one2many('project.branch.merge.comment', 'merge_id', 'Comments'),
        'file_ids':fields.one2many('project.branch.merge.files', 'merge_id', 'Files Changed'),
        'active':fields.boolean('Active'),
        'branch_type':fields.related('branch_id', 'branch_type', type="selection", selection=[('fix','Bug Fix'), ('feature','Feature'), ('improvement','Improvements'), ('junk','Need Review'), ('not_clean','Junk')], string='Type', store=True),
    }

    def create_comments(self, cr, uid, merge, merge_id, context=None):
        comment_pool = self.pool.get('project.branch.merge.comment')
        for comment in merge.all_comments:
            comment_id = comment_pool.search(cr, uid, [('ref_id','=',comment.id)])
            if comment_id:
                continue

            user_id = False
            lp_user = comment.author
            if lp_user:
                user_id = get_user(self, cr, uid, lp_user, context)

            vals = {
                'web_link':comment.web_link,
                'ref_id':comment.id,
                'merge_id':merge_id,
                'name':comment.title,
                'description':comment.message_body,
                'user_id':user_id,
                'state':comment.vote,
                'date_created':comment.date_created
            }
            comment_pool.create(cr, uid, vals)
        return True

    def crete_diff_files(self, cr, uid, merge, merge_id, context={}):
        file_pool = self.pool.get('project.branch.merge.files')
        diff = merge.preview_diff.diffstat

        for file in diff:
            if '.po' in file:
                continue
            vals = {
                'name':file,
                'add_line':diff[file][0],
                'remove_line':diff[file][1],
                'merge_id':merge_id
            }
            file_pool.create(cr, uid, vals, context)
        return True

    def update_merge_proposals(self, cr, uid, ids, context=None):
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()

        if not ids:
            ids = self.search(cr, uid, [('state','in',['Work in progress', 'Needs review'])])

        global users

        counter = 0
        _logger.info('%s proposals selected to update status' % (len(ids)))
        for proposal in self.browse(cr, uid, ids, context):
            counter += 1
            merge = False
            try:
                branch_url = proposal.web_link.replace(CODE_LINK, LP_API_LINK)
                merge = launchpad.load(branch_url)
            except Exception, ex:
                _logger.error('Merge %s : Problem in loading proposal %s' % (counter, branch_url))
                self.write(cr, uid, [proposal.id],{'active':False})
                cr.commit()
                continue

            vals = {
                'date_reviewed':merge.date_reviewed,
                'description':merge.description,
                'state':merge.queue_status
            }
            self.write(cr, uid, [proposal.id], vals, context)
            self.create_comments(cr, uid, merge, proposal.id, context)
            _logger.info('Merge %s : status updated for %s ' % (counter, branch_url))
            if counter % 10 == 0:
                cr.commit()

    def get_merge_proposals(self, cr, uid, ids, context=None):
        new_merge = []
        new_project = []
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()

        global users
        users = {}

        project_pool = self.pool.get('project.project')
        branch_pool = self.pool.get('project.branch')
        user_pool = self.pool.get('res.users')

        project_ids = project_pool.search(cr, uid, [('state','=','open')])

        for oeproject in project_pool.browse(cr, uid, project_ids):
            if oeproject.child_ids:
                continue

            _logger.info('Connection to project %s' % (oeproject.name))
            proposals = []

            try:
                project = launchpad.projects[oeproject.name]
                if project:
                    proposals = project.getMergeProposals(status=['Work in progress', 'Approved', 'Needs review', 'Rejected', 'Merged', 'Code failed to merge', 'Queued', 'Superseded'])
                    #proposals = project.getMergeProposals()
                else:
                    _logger.error('Project not available on Launchpad %s' % (oeproject.name))
                    continue
            except Exception, ex:
                _logger.error('Project not available on Launchpad %s' % (oeproject.name))
                continue

            new_project.append(oeproject.name)
            merge_cache = {}
            ids = self.search(cr, uid, [('project_id','=',oeproject.id)])
            for merge in self.read(cr, uid, ids, ['web_link'], context):
                merge_cache[merge['web_link']] = merge['id']

            _logger.info('%s merge proposals selected to process' % (len(proposals)))

            counter = 0
            for merge in proposals:
                counter += 1

                if merge_cache.get(merge.web_link, 0) > 0:
                    _logger.warning('Merge %s : merge proposal exist %s' % (counter, merge))
                    continue

                vals = {}
                diff = merge.preview_diff

                lp_user = merge.registrant
                user_id = False
                if lp_user:
                    user_id = get_user(self, cr, uid, lp_user, context)

                lp_user = merge.reviewer
                reviewer_user_id = False
                if lp_user:
                    reviewer_user_id = get_user(self, cr, uid, lp_user, context)

                target = merge.target_branch.unique_name
                target_id = branch_pool.search(cr, uid, [('name','=',target)])

                source = merge.source_branch.unique_name
                branch_id = branch_pool.search(cr, uid, [('name','=',source)])

                if len(target_id) == 0 or len(branch_id) == 0:
                    _logger.error('Merge %s : Project branches is not available in openerp %s' % (counter, source))
                    continue

                name = "%s => %s" % (merge.source_branch.unique_name, merge.target_branch.unique_name)
                vals.update({
                    'project_id':oeproject.id,
                    'branch_id':branch_id[0],
                    'web_link':merge.web_link,
                    'date_created':merge.date_created,
                    'date_reviewed':merge.date_reviewed,
                    'description':merge.description,
                    'name':name,
                    'state':merge.queue_status,
                    'user_id':user_id,
                    'reviewer_user_id':reviewer_user_id,
                    'target_branch_id':target_id[0],
                    'active':True
                })

                if diff:
                    diff_text = "/"
                    diff_link = False
                    diff_vals = {
                        'added_lines_count':0,
                        'removed_lines_count':0,
                        'diff_lines_count':0,
                        'diff_text':"/",
                        'conflicts':"/",
                        'diff_link':"/",
                        'diff_file_count':0
                    }
                    try:
                        diff_link = "%s lines (+%s/-%s) %s files modified" %(diff.diff_lines_count, diff.added_lines_count, diff.removed_lines_count, len(diff.diffstat))
                        diff_vals.update({
                            'added_lines_count':diff.added_lines_count,
                            'removed_lines_count':diff.removed_lines_count,
                            'diff_lines_count':diff.diff_lines_count,
                            'diff_text':diff_text,
                            'conflicts':diff.conflicts,
                            'diff_link':diff_link,
                            'diff_file_count':len(diff.diffstat)
                        })
                    except:
                        _logger.error('Merge %s : Problem in merge proposal %s' % (counter, merge))
                    vals.update(diff_vals)

                merge_id = self.create(cr, uid, vals)
                new_merge.append(name)
                self.create_comments(cr, uid, merge, merge_id, context)
                if diff and vals['diff_file_count'] != 0:
                    self.crete_diff_files(cr, uid, merge, merge_id, context)

                _logger.info('Merge %s : processed %s' % (counter, merge))
                if (counter % 10)== 0:
                    cr.commit()
        if oeproject.action_id:
            message = """Hello !,
We have just processed %(project)s project to get the new merge proposal and we get %(total)s new merge proposals.

List of projects processed :
%(projects)s

Here are the list of new merge proposals :
%(message)s

Regards,
OpenERP Development Team"""
            msg = '\n'.join(str(v) for v in new_merge)
            projects = '\n'.join(str(v) for v in new_project)
            message = message % {'project':len(new_project), 'projects':projects, 'total':str(len(new_merge)), 'message':msg}
            project_pool.write(cr, uid, [oeproject.id], {'log':message})
            cr.commit()
            self.pool.get('ir.actions.server').run(cr, uid, [oeproject.action_id.id], {'active_id':oeproject.id, 'active_ids':[oeproject.id], 'active_model':'project.project'})

        return True

project_branch_merge_proposal()

class project_branch_merge_proposal_comment(osv.osv):
    _name = 'project.branch.merge.comment'
    _description = 'Merge Proposal Comments'

    _columns = {
        'ref_id':fields.integer('Comment Reference'),
        'merge_id':fields.many2one('project.branch.merge', 'Merge Proposal'),
        'name':fields.char('Name', size=1024),
        'description':fields.text('Message'),
        'user_id':fields.many2one('res.users', 'Owner'),
        'date_created':fields.datetime('Created On'),
        'state':fields.selection(REVIEW_STATE, 'State'),
        'web_link':fields.char('Web Link', size=2048)
    }
project_branch_merge_proposal_comment()

class project_branch_merge_proposal_files(osv.osv):
    _name = 'project.branch.merge.files'
    _description = 'Merge Proposal Files'

    _columns = {
        'add_line':fields.integer('Lines Added'),
        'remove_line':fields.integer('Lines Removed'),
        'merge_id':fields.many2one('project.branch.merge', 'Merge Proposal'),
        'name':fields.char('Name', size=1024),
    }
project_branch_merge_proposal_comment()

class project_bug_tag(osv.osv):
    _name = 'project.bug.tag'
    _description = 'Project Bug Tag'

    _columns = {
        'name':fields.char('Name', size=1024),
        'description':fields.text('Description'),
    }
project_bug_tag()

class project_bug(osv.osv):
    _name = 'project.bug'
    _description = 'Project Bug'
    _order = "date_created desc"

    _columns = {
        'project_id':fields.many2one('project.project', 'Project'),
        'web_link':fields.char('Web Link', size=2048),
        'name':fields.char('Name', size=1024),
        'date_created':fields.datetime('Reported On'),
        'date_assigned':fields.datetime('Assign On'),
        'date_closed':fields.datetime('Closed On'),
        'date_fix_committed':fields.datetime('Fixed On'),
        'date_fix_released':fields.datetime('Released On'),
        'date_in_progress':fields.datetime('Start working by'),
        'user_id':fields.many2one('res.users', 'Reported By'),
        'assign_user_id':fields.many2one('res.users', 'Assigned To'),
        'description':fields.text('Message'),
        'state':fields.selection(BUG_STATUS, 'State'),
        'importance':fields.selection(BUG_IMPORTANCE, 'Importance'),
        'comment_ids':fields.one2many('project.bug.comment', 'bug_id', 'Activities'),
        'tags':fields.many2many('project.bug.tag', 'rel_bug_tags', 'bug_id', 'tag_id', 'Tags'),
        'milestone':fields.char('Milestone', size=32),
        'branch_ids':fields.one2many('project.branch', 'bug_id', 'Branch'),
        'active':fields.boolean('Active')
    }

    def link_branches(self, cr, uid, bug_id, branches, context):
        branch_pool = self.pool.get('project.branch')
        for branch in branches:
            if branch.branch:
                branch_ids = branch_pool.search(cr, uid, [('name','=',branch.branch.unique_name)])
                if branch_ids:
                    branch_pool.write(cr, uid, branch_ids, {'bug_id':bug_id})
        return True

    def create_comments(self, cr, uid, bug_id, comments, context=None):
        comment_pool = self.pool.get('project.bug.comment')
        for comment in comments:
            comment_ids = comment_pool.search(cr, uid, [('http_etag','=',comment.http_etag)])
            if comment_ids:
                continue

            vals = {
                'bug_id':bug_id,
                'date_created':comment.datechanged,
                'web_link':comment.web_link,
                'http_etag':comment.http_etag
            }

            lp_user = comment.person
            if lp_user:
                user_id = get_user(self, cr, uid, lp_user, context)
                vals.update({'user_id':user_id})

            name = comment.newvalue
            if comment.oldvalue and comment.newvalue:
                name = "%s => %s" % (comment.oldvalue, comment.newvalue)

            vals.update({'name':name})
            comment_pool.create(cr, uid, vals, context)

    def create_messages(self, cr, uid, bug_id, messages, context=None):
        comment_pool = self.pool.get('project.bug.comment')
        for message in messages:
            comment_ids = comment_pool.search(cr, uid, [('web_link','=',message.web_link)])
            if comment_ids:
                continue

            vals = {
                'bug_id':bug_id,
                'date_created':message.date_created,
                'web_link':message.web_link,
                'http_etag':message.http_etag
            }

            lp_user = message.owner
            if lp_user:
                user_id = get_user(self, cr, uid, lp_user, context)
                vals.update({'user_id':user_id})

            if message.subject:
                vals.update({'name':message.subject})

            if message.content:
                vals.update({'content':message.content})

            comment_pool.create(cr, uid, vals, context)

    tags = {}
    def link_tags(self, cr, uid, lptags, context):
        ids = []
        tag_pool = self.pool.get('project.bug.tag')
        for tag in lptags:
            tag_id = tags.get(tag, False)
            if not tag_id:
                tag_id = tag_pool.create(cr, uid, {'name':tag})
                tags[tag] = tag_id
            ids.append(tag_id)
        return [(6, 0, ids)]

    def update_launchpad_bugs(self, cr, uid, ids, context=None):
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()

        full_update = True
        if not ids:
            ids = self.search(cr, uid, [('state','not in',['Fix Released', 'Fix Committed'])])
            full_update = False

        global users
        users = {}

        counter = 0
        _logger.info('%s bugs selected to update status' % (len(ids)))
        for lpbug in self.browse(cr, uid, ids, context):
            counter += 1
            bug = False
            branch_url = False
            try:
                branch_url = lpbug.web_link.replace(BUG_LINK, LP_API_LINK)
                bug = launchpad.load(branch_url)
            except Exception, ex:
                _logger.error('Bug %s : problem in loading %s' % (counter, branch_url))
                self.write(cr, uid, [lpbug.id],{'active':False})
                cr.commit()
                continue

            if lpbug.state == bug.status:
                _logger.warning('Bug %s - No change in status %s its %s' % (counter, bug, bug.status))
                continue

            vals = {
                'date_assigned':bug.date_assigned,
                'date_closed':bug.date_closed,
                'date_fix_committed':bug.date_fix_committed,
                'date_fix_released':bug.date_fix_released,
                'date_in_progress':bug.date_in_progress,
                'state':bug.status,
                'importance':bug.importance
            }

            milestone = lpbug.project_id.name
            if bug.milestone:
                milestone = "%s-%s" % (milestone, bug.milestone.name)

            vals.update({'milestone':milestone})

            lp_user = bug.assignee
            if lp_user:
                assign_user_id = get_user(self, cr, uid, lp_user, context)
                vals.update({'assign_user_id':assign_user_id})

            update = self.write(cr, uid, [lpbug.id], vals, context)
            if full_update:
                if update and bug.bug.activity:
                    self.create_comments(cr, uid, lpbug.id, bug.bug.activity, context)

                if update and bug.bug.messages:
                    self.create_messages(cr, uid, lpbug.id, bug.bug.messages, context)

                if update and bug.bug.linked_branches:
                    self.link_branches(cr, uid, lpbug.id, bug.bug.linked_branches, context)

            if counter % 10 == 0:
                cr.commit()
        _logger.info('Bug %s - status updated for %s to %s' % (counter, bug, bug.status))
        return True

    def get_launchpad_bugs(self, cr, uid, ids, context=None):
        _logger.info('Initialize Launchpad login.')
        launchpad = get_launchpad()

        new_project = []
        new_bugs = []

        global users
        users = {}

        global tags
        tags = {}

        project_pool = self.pool.get('project.project')
        user_pool = self.pool.get('res.users')
        tag_pool = self.pool.get('project.bug.tag')

        project_ids = project_pool.search(cr, uid, [('state','=','open')])

        tag_ids = tag_pool.search(cr, uid, [])
        for tag in tag_pool.browse(cr, uid, tag_ids, context):
            tags[tag.name] = tag.id

        for oeproject in project_pool.browse(cr, uid, project_ids):
            if oeproject.child_ids:
                continue

            _logger.info('Connection to project %s' % (oeproject.name))
            bugs = []

            try:
                project = launchpad.projects[oeproject.name]
                if project:
                    bugs = project.searchTasks(status = ['New', 'Incomplete', 'Triaged', 'Opinion', 'Invalid', 'Won\'t Fix', 'Confirmed', 'In Progress', 'Fix Committed', 'Fix Released'])
                else:
                    _logger.error('Project not available on Launchpad %s' % (oeproject.name))
                    continue
            except Exception, ex:
                _logger.error('Project not available on Launchpad %s \n %s' % (oeproject.name, ex))
                continue

            _logger.info('%s bugs to process for %s project' % (len(bugs), oeproject.name))

            new_project.append(oeproject.name)
            bug_cache = {}
            ids = self.search(cr, uid, [('project_id','=',oeproject.id)])
            for bug in self.read(cr, uid, ids, ['web_link'], context):
                bug_cache[bug['web_link']] = bug['id']

            counter = 0
            for bug in bugs:
                counter += 1

                if bug_cache.get(bug.web_link, 0) > 0:
                    _logger.warning('Bug %s : already exist %s' % (counter, bug))
                    continue

                _logger.info('Bug %s : processing %s' % (counter, bug))
                vals = {
                    'project_id':oeproject.id,
                    'web_link':bug.web_link,
                    'date_created':bug.date_created,
                    'date_assigned':bug.date_assigned,
                    'date_closed':bug.date_closed,
                    'date_fix_committed':bug.date_fix_committed,
                    'date_fix_released':bug.date_fix_released,
                    'date_in_progress':bug.date_in_progress,
                    'name':bug.bug.title,
                    'description':bug.bug.description,
                    'state':bug.status,
                    'importance':bug.importance,
                    'active':True
                }

                milestone = "/"
                if bug.milestone:
                    milestone = bug.milestone.name

                vals.update({'milestone':milestone})

                if bug.bug.tags:
                    vals.update({'tags':self.link_tags(cr, uid, bug.bug.tags, context)})

                lp_user = bug.owner
                if lp_user:
                    user_id = get_user(self, cr, uid, lp_user, context)
                    vals.update({'user_id':user_id})

                lp_user = bug.assignee
                if lp_user:
                    assign_user_id = get_user(self, cr, uid, lp_user, context)
                    vals.update({'assign_user_id':assign_user_id})

                new_bugs.append(bug.bug.title)
                bug_id = self.create(cr, uid, vals, context)

                if counter % 10 == 0:
                    cr.commit()

        if oeproject.action_id:
            message = """Hello !,
We have just processed %(project)s project to get the new bugs and we get %(total)s new bugs reported.

List of projects processed :
%(projects)s

Here are the list of new Bugs reported :
%(message)s

Regards,
OpenERP Development Team"""
            msg = '\n'.join(str(v) for v in new_bugs)
            projects = '\n'.join(str(v) for v in new_project)
            message = message % {'project':len(new_project), 'projects':projects, 'total':str(len(new_bugs)), 'message':msg}
            project_pool.write(cr, uid, [oeproject.id], {'log':message})
            cr.commit()
            self.pool.get('ir.actions.server').run(cr, uid, [oeproject.action_id.id], {'active_id':oeproject.id, 'active_ids':[oeproject.id], 'active_model':'project.project'})

        return True

project_bug()

class project_branch_inherit(osv.osv):
    _inherit = 'project.branch'

    _columns = {
        'bug_id':fields.many2one('project.bug', 'Bug')
    }
project_branch_inherit()

class project_project_bug_comment(osv.osv):
    _name = 'project.bug.comment'
    _description = 'Bug Comments'
    _order = "date_created"

    _columns = {
        'bug_id':fields.many2one('project.bug', 'Bug'),
        'name':fields.char('Activity', size=1024),
        'content':fields.text('Message'),
        'user_id':fields.many2one('res.users', 'Owner'),
        'date_created':fields.datetime('Created On'),
        'web_link':fields.char('Web Link', size=2048),
        'http_etag':fields.char('eTage', size=2048),
    }
project_project_bug_comment()

class project_launchpad_event(osv.osv):
    _name = "project.launchpad.event"
    _description = "Launchpad events"
    _columns = {
        'name':fields.char('Name', size=128),
        'email':fields.text('Email'),
        'date_created':fields.datetime('Event Date')
    }

    def send_email(self, cr, uid, ids, context):

        return True
project_launchpad_event()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
