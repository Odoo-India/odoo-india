# -*- coding: utf-8 -*-
from openerp import http
from openerp.http import request


class WebsiteGodaddy(http.Controller):

    @http.route('/godaddy/domain', type='http', auth="public", website=True)
    def godaddy(self, domains=False, **post):
        value = {'available': False}
        return request.website.render("website_godaddy.index", value)
