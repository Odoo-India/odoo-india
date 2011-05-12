
##############################################################################
#    Copyright 2011, SG E-ndicus Infotech Private Limited ( http://e-ndicus.com )
#    Contributors: Selvam - selvam@e-ndicus.com
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
###############################################################################


{
    'name': 'TDS management for India',
    'version': '1.0',
    #'category': 'Generic Modules/CRM & SRM/Inhouse Service',
    'description': """
To handle Tax Deduction at Source 
TDS Process:
Deductee (Seller) provides Services and Bill to the Deductor (Buyer)
Deductor makes the payment after deducting TDS
Deductor remits the TDS amount into Bank (Treasury)
Bank (Treasury) remit the amount to the Government Account
Deductor Issues Form 16A to Deductee for the TDS amount deducted
Deductor Files the e-TDS to NSDL
Deductee Files the Return with Form 16A to Income tax Department.


Masters :
Sections
Nature Of Payment
Deductee Type

Features:
TDS linked with Invoice Line
Accounting TDS and Deduction
TDS with Lower and Zero Rate
Accounting TDS and Deducting it Later
TDS Helper for paying TDS to Govt
Viewing TDS Pending, payable, zero/reduced rate

Reports:
Form 16A
Form 26Q
Form 26Q Annexure
Form 26A
Form 26A Annexure


Todo:
Invoice for Later TDSes
Advance payments
Surcharge calculation on prior period
Reversal of TDS
Accounting changes in TDS %
Any statment filed field in 26Q and 27Q
     """,
    'author': 'Selvam(selvam@e-ndicus.com)',
    'website': 'http://e-ndicus.com',
    'depends': ['base','account','account_voucher','account_voucher_cheque'],
    'init_xml': [
],
    'update_xml': ['account_view.xml','tds_view.xml','wizard/tds_helper.xml','partner_address_view.xml'],
    'demo_xml': [
],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
