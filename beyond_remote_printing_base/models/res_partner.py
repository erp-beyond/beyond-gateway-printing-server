# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    zpl_content_id =  fields.One2many(comodel_name='label.content',inverse_name='partner_id')
    
    
    def _get_zpl_content(self,label_type):
        self.ensure_one()
        res = ''
        
        zpl_contents = self.zpl_content_id.filtered(lambda c: label_type in c.label_type_id and c.use)
        
        for content in zpl_contents:
            
            raw_content = content.zpl_data.replace('^XA^FO0,0','').replace('^XZ','')
            res += '^FO%s,%s%s'%(content.x_pos,content.y_pos,raw_content)
        
        return res