# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
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
# Version 1.0 Philmer
import xlwt 

def font_style(position='left',bold=0, fontos=0, font_height=200,border=0,color=False):
    font = xlwt.Font()
    font.name = 'Verdana'
    font.bold = bold
    font.height=font_height
    center = xlwt.Alignment()
    center.horz = xlwt.Alignment.HORZ_CENTER
    center.vert = xlwt.Alignment.VERT_CENTER
    center.wrap = xlwt.Alignment.VERT_JUSTIFIED
    left = xlwt.Alignment()
    left.horz = xlwt.Alignment.HORZ_LEFT
    left.vert = xlwt.Alignment.VERT_CENTER
    left.wrap = xlwt.Alignment.VERT_JUSTIFIED
    
    borders = xlwt.Borders()
    borders.right = 1
    borders.left=1
    borders.top = 1
    borders.bottom = 1
    

    
    orient = xlwt.Alignment()
    orient.orie = xlwt.Alignment.ORIENTATION_90_CC
    
    style = xlwt.XFStyle()
    
    if border == 1:
        style.borders = borders
    
    if fontos == 'red' :
        font.colour_index = 2
        style.font = font
    else: style.font = font

    if position == 'center' :
        style.alignment = center
    else : 
        style.alignment = left
    if color =='grey':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 22
        style.pattern = badBG
    if color =='red':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 5
        style.pattern = badBG
        
    if color =='yellow':
        badBG = xlwt.Pattern()
        badBG.pattern = badBG.SOLID_PATTERN 
        badBG.pattern_fore_colour = 0x0D
        style.pattern = badBG
              
    return style
