# -*- coding: utf-8 -*-

import uuid

from odoo import api, fields, models


class MailRemoteCommand(models.Model):
    _name = 'mail.remote.command'

    name = fields.Char(required=True)
    channel_id = fields.Many2one('mail.channel', string='Post to channel', required=True)
    request_method = fields.Selection([('get', 'GET'), ('post', 'POST')], string="Request Method", required=True, default='post')
    url = fields.Char(string="Request URL", required=True)
    token = fields.Char(string="Token", default=uuid.uuid4().hex, readonly=True)

    @api.multi
    def generate_new_token(self):
        self.ensure_one()
        self.token = uuid.uuid4().hex
