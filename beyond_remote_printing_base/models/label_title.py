from odoo import models, fields,api,_
from odoo.exceptions import UserError

class LabelTitle(models.Model):
    _name = 'label.title'
    _description = 'Label Title'

    key = fields.Char(name='key',readonly=True)
    value = fields.Text(translate=True,required=True)
    
    _sql_constraints = [
        ('key_unique', 'unique(key)', 'The key must be unique!')
    ]
    
    @api.model
    def _get_title(self,key):
        
        if not key:
            raise UserError('No Key set to get label title')
        
        candidate = self.search([('key','=',key)],limit=1)
        if not candidate:
            candidate = self.create({'key':key,'value':key})
            
        return candidate