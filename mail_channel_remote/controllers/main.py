# -*- coding: utf-8 -*-

from odoo.addons.web import http
from odoo.http import request


class RemoteCommandCallback(http.Controller):

    @http.route(['/web/live/callback'], type='http', method='post', auth='public', csrf=False)
    def live_callback(self, **kwargs):
        if kwargs.get('image'):
            message = "<img src='" + kwargs['image'] + "' height='200' width='200'/>"
        else:
            message = kwargs.get('message')
        if kwargs.get('token'):
            remote = request.env['mail.remote.command'].sudo().search([("token", "=", kwargs['token'])])
            remote.channel_id.sudo().message_post(body=message, message_type='comment', subtype='mail.mt_comment', content_subtype='html')
        return
