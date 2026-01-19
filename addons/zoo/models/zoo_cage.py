# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ZooCage(models.Model):
    _name = 'zoo.cage'
    _description = 'Zoo Cage'
    _order = 'name'

    name = fields.Char(string='Cage Name',
        required=True,
        help='Name of the cage')
    
    capacity = fields.Integer(string='Capacity',
        help='Maximum number of animals')
    
    location = fields.Char(string='Location')
    
    cage_type = fields.Selection([
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('aquarium', 'Aquarium'),
        ('aviary', 'Aviary'),
        ],
        string='Cage Type',
        default='outdoor',
        required=True)
    
    area = fields.Float(string='Area (m²)',
        help='Cage area in square meters')
    
    description = fields.Text(string='Description',
        help='Description of the cage')
    
    active = fields.Boolean(string='Active',
        default=True)

    # Định nghĩa một Standard checklist
    checklist_template_ids = fields.One2many(
        'zoo.cage.checklist.template', 
        'cage_id', 
        string='Standard Checklist'
    )

# Định nghĩa một Standard checklist
class ZooCageChecklistTemplate(models.Model):
    _name = 'zoo.cage.checklist.template'
    _description = 'Cage Standard Task Template'
    
    cage_id = fields.Many2one(comodel_name='zoo.cage',
        string='Cage')
    
    name = fields.Char(string='Task Description',
        required=True)
    
    required = fields.Boolean(string='Required',
        default=True)    
