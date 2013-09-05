#!/usr/bin/python
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
import optparse
from lazr.restfulclient.errors import HTTPError
from launchpadlib.credentials import Credentials

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

def generate_credentials(app_name, file_name):
    credentials = Credentials(app_name)
    request_token_info = credentials.get_request_token(web_root="production")
    _logger.info('Copy and open %s in browser and follow the instruction. Do not close this program until you approve the request', request_token_info)
    complete = False
    while not complete:
        try:
            credentials.exchange_request_token_for_access_token(web_root="production")
            complete = True
        except HTTPError, e:
            pass

    credentials.save_to_path(file_name)
    _logger.info('credentials for %s saved to %s successfully', app_name, file_name)

def main():
    p = optparse.OptionParser(usage="%prog --app-name=OpenERP --file-path=./openerp-lp.txt", version="%prog 1.0")
    p.add_option('--app-name', '-a')
    p.add_option('--file-path', '-f')
    options, arguments = p.parse_args()

    if options.app_name and options.file_path:
        generate_credentials(options.app_name, options.file_path)
    else:
        print "lp-token.py --app-name=OpenERP --file-path=./openerp-lp.txt"
    
if __name__ == "__main__":
    main()
