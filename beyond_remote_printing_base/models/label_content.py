from odoo import _, api, fields, models

class LabelContent(models.Model):
    _name = 'label.content'
    _description = 'Label Content'
    
    name = fields.Char()
    partner_id = fields.Many2one(comodel_name='res.partner')
    label_type_id = fields.Many2many(comodel_name='label.type')
    zpl_data = fields.Char(string='ZPL data',required=True)
    x_pos = fields.Integer()
    y_pos = fields.Integer()
    font_size = fields.Integer()
    use = fields.Boolean(default=True)
    
    