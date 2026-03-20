from odoo import _, api, fields, models
from odoo.exceptions import UserError

class LabelType(models.Model):
    _name = 'label.type'
    _description = 'Label Type'
    
    name = fields.Char(required=True,readonly=False)
    key = fields.Char(required=True,readonly=True)
    
    label_home_x_rotate = fields.Integer(required=True,default=0)
    label_home_y_rotate = fields.Integer(required=True,default=0)
    
    _sql_constraints = [
        ('key_unique', 'unique(key)', 'The key must be unique!')
    ]
    
    @api.model
    def _get_label_type(self,key):
        
        if not key:
            raise UserError('No Key set to get label title')
        
        candidate = self.search([('key','=',key)],limit=1)            
        return candidate
    