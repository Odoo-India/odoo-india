# -*- coding: utf-8 -*-

import re
import requests

from odoo import api, models


class MailChannel(models.Model):
    _inherit = 'mail.channel'

    @api.multi
    def post_text_to_remote(self, url=None, command=None, method=None, token=None, **kwargs):
        self.ensure_one()
        parameters = {}
        Params = self.env['ir.config_parameter'].sudo()
        callback_url = '%s/%s' % (Params.get_param('web.base.url'), 'web/live/callback')
        parameters['token'] = token
        if command:
            parameters['command'] = command
        if method == "get":
            r = requests.get(url, params=callback_url, headers=parameters)
            r.raise_for_status()
            return r
        else:
            r = requests.post(url, params=callback_url, headers=parameters)
            r.raise_for_status()
            return r
        return False

    @api.multi
    @api.returns('self')
    def message_post(self, body='', subject=None, message_type='notification', subtype=None, parent_id=False, attachments=None, content_subtype='html', **kwargs):
        self.ensure_one()
        res = None
        self.filtered(lambda channel: channel.channel_type == 'chat').mapped('channel_last_seen_partner_ids').write({'is_pinned': True})
        remote = self.env['mail.remote.command'].search([('channel_id', '=', self.id)])
        for command in remote:
            text = re.subn(command.name, '', body, re.I)
            if text[1]:
                res = self.post_text_to_remote(url=command.url, command=text[0], method=command.request_method,token=command.token)
        if not res:
            return super(MailChannel, self.with_context(mail_create_nosubscribe=True)).message_post(body=body, subject=subject, message_type=message_type, subtype=subtype, parent_id=parent_id, attachments=attachments, content_subtype=content_subtype, **kwargs)
        return self
