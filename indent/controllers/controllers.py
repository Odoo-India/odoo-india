# -*- coding: utf-8 -*-
from openerp import http

# class Indent(http.Controller):
#     @http.route('/indent/indent/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/indent/indent/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('indent.listing', {
#             'root': '/indent/indent',
#             'objects': http.request.env['indent.indent'].search([]),
#         })

#     @http.route('/indent/indent/objects/<model("indent.indent"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('indent.object', {
#             'object': obj
#         })