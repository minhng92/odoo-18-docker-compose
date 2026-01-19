# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class ZooAnimalBackup(models.Model):
    _name = "zoo.animal.backup" # Tên mới
    _inherit = "zoo.animal" # Tên chính xác của model cha
    _description = "Backup animal model"
    
    backup_code = fields.Char("Backup Code",
        required=True) # eg. BK200925, BK201001, ...

    toy_ids = fields.Many2many(comodel_name='product.product',
        string="Toys BK",
        relation='animal_bk_product_toy_rel',
        column1='col_animal_bk_id',
        column2='col_product_id')