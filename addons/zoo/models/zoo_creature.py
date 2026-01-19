# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ZooCreature(models.Model):
    _name = "zoo.creature"
    _description = "Creature"
    
    name = fields.Char(string='Name',
        required=True)
    
    environment = fields.Selection([
        ('water', 'Water'),
        ('ground', 'Ground'),
        ('sky', 'Sky'),
        ('ocean', 'Ocean'),
        ('forest', 'Forest'),
        ('desert', 'Desert'),
        ('mountain', 'Mountain'),
        ('river', 'River'),
        ('lake', 'Lake'),
        ('pond', 'Pond'),
        ('sea', 'Sea'),
        ('cool', 'Cool'),
        ],
        string='Environment',
        default='ground')
    
    is_rare = fields.Boolean('Is Rare',
        default=False)
    
    animal_ids = fields.One2many(comodel_name='zoo.animal',
        inverse_name='creature_id',
        string='Animals')
    
    animal_count = fields.Integer(string='Animal Count',
        compute='_compute_animal_count',
        store=True)
    
    allowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        relation='zoo_creature_product_rel',
        column1='creature_id',
        column2='product_id',
        string='Allowed Food Products',
        help='List of food products that can be fed to this species'
    )
    
    # Định nghĩa các hàm tính toán
    @api.depends('animal_ids')
    def _compute_animal_count(self):
        for record in self:
            record.animal_count = len(record.animal_ids)