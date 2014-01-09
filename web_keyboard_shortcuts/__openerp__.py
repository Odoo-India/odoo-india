# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

{
    'name': 'Keyboard Shortcuts',
    'version' : '1.0',
    'author' : 'OpenERP SA',
    'category': 'Tools',
    'description': """
Shortcuts and GUI Improvement.
==============================
An attractive GUI design for your interface gives you a smart look for main menus. A list of keyboard shortcuts provides you an easy way to handle the different operations. You can also search quickly on menus listed in shortcuts by simply pressing characters on the keyboard and get the filtered records on your list.

Shortcuts: 
----------
    * **Ctrl + S** -  For Save Current Object(Require:form in edit mode)
    * **Ctrl + E** -  For Edit Current Object(Require:form in saved mode)
    * **Ctrl + space** -  For Create New Record(Open Form).
    * **Alt** -  In Form View Press Alt key and then press Access Key Passed from Button.
    * **Ctrl + K** -  Switch to Kanban View.
    * **Ctrl + L** -  Switch to List View.
    * **Ctrl + ;** -  Switch to Form View.
    * **Ctrl + F** -  Focus on Search view(Press This shortcut and start searching).
    * **Ctrl + D** -  Disable search view (Hide search view).
    * **Ctrl + >** -  Display Next Page(In Form View).
    * **Ctrl + <** -  Display Previous Page(In Form View).
    * **Ctrl + Backspace** -  Go in to on step back on breadcrumb (Example **Sales Orders / SO007 / Invoice** if you press this shortcut then you will come back at S0007).
    * **Ctrl + Esc** -  For Discard Current Change (Effect Like press Discard Link)
    * **Ctrl + ↓ (Down Arrow)** -  Expand lines(Need Group By in Tree View ).
    * **Ctrl + ↑ (Up Arrow)** -  Collapse All lines(Need Group By in Tree View ).
    * **Ctrl + 1 to Ctrl + 9** -  Change Main Menu according to Number Pressed.
    * **For Secondary Menu** -  Press **Ctrl + `** (Key above Tab) and then press ↑ or ↓ for movement and then Press Enter
    * **Ctrl + P** -  Give Screenshots of Tree Or Form Or Graph ( Without Menus ).
    * **Ctrl + F11** -  Enable Full Screen Mode.
    * **Esc** -  Disable Full Screen Mode.

Search Hint: 
------------
After installing Search View supports hints. You can redirect to any menu from search view.

**How to use**
    * Add any tree in to shortcut(with help of star)
    * Now open search view and type first character of name of view. Ex.You added "Sales/Sales/Customers" shortcut then type "C"(case sensitive).this will shows a hint. 
    * Now press right arrow key and then press enter, you will redirect to that view.

You can also custom hints from Menu: **Setting > Technical > User Interface > Search Hint Setup**
    """,
    "author": "OpenERP SA",
    "website": "http://www.openerp.com",
    'depends': ["base","web_shortcuts","web_gui"],
    'init_xml': [],
    'data': [
             "ir_ui_menu_view.xml"
             ],
        'css':[
        'static/src/css/focus_menu.css',
    ],
    "js" : [
        "static/src/js/html2canvas.js",
        "static/src/js/jquery.cookie.js",
        "static/src/js/web_keyboard_shortcuts.js",
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
