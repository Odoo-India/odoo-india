# -*- coding: utf-8 -*-

from odoo import models, fields


class GodaddyClient(models.Model):
    _inherit = "website"

    godaddy_api_key = fields.Char(string='Godaddy API key')
    godaddy_api_secret = fields.Char(string='Godaddy API secret')
