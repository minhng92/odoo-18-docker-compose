# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import datetime


class ZooAnimal(models.Model):
    _name = "zoo.animal"
    _description = "Animal in the zoo"

    name = fields.Char(
        string='Animal Name',
        required=True)    

    description = fields.Text(string='Description')

    dob = fields.Date(
        string='DOB',
        required=False)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
        ],
        string='Gender',
        default='male',
        required=True)

    feed_time = fields.Datetime(
        string='Feed Time',
        copy=False)
    
    is_alive = fields.Boolean('Is Alive',
        default=True)
    
    image = fields.Binary("Image",
        attachment=True,
        help="Animal Image")
    
    weight = fields.Float('Weight (kg)')
    
    weight_pound = fields.Float('Weight (pounds)')
    
    introduction = fields.Text('Introduction (EN)')
    
    nickname = fields.Char('Nickname')
    
    introduction_vn = fields.Html('Introduction (VI)')
    
    is_purchased = fields.Boolean('Has Been Purchased',
        default=False)
    purchase_price = fields.Float('Purchase Price')
    
    veterinarian_id = fields.Many2one(comodel_name='res.partner',
        string='Veterinarian')
    
    age = fields.Integer('Pet Age',
        compute='_compute_age')
    
    number_of_children = fields.Integer('Number of Children',
        compute='_compute_number_of_children')
    
    mother_id = fields.Many2one(comodel_name='zoo.animal',
        string='Mother',
        ondelete='set null') # ondelete: 'set null', 'restrict', 'cascade'
    
    mother_name = fields.Char('Mother Name',
        related='mother_id.name')
    
    female_children_ids = fields.One2many(comodel_name='zoo.animal',
        inverse_name='mother_id',
        string='Female Children')
    
    father_id = fields.Many2one(comodel_name='zoo.animal',
        string='Father',
        ondelete='set null')
    
    father_name = fields.Char('Father Name',
        related='father_id.name')
    
    male_children_ids = fields.One2many(comodel_name='zoo.animal',
        inverse_name='father_id',
        string='Male Children')


    toy_ids = fields.Many2many(comodel_name='product.product',
        string="Toys",
        relation='animal_product_toy_rel',
        column1='col_animal_id',
        column2='col_product_id')

    creature_id = fields.Many2one(comodel_name='zoo.creature',
        string='Creature')

    cage_id = fields.Many2one(comodel_name='zoo.cage',
        string='Cage',
        ondelete='set null')

    # --- Các hàm tính toán (Compute Functions) ---
    @api.depends('dob')
    def _compute_age(self):
        now = datetime.datetime.now()
        current_year = now.year
        for record in self:
            dob = record.dob
            if dob:
                dob_year = dob.year
                delta_year = current_year - dob_year
                if delta_year < 0:
                    raise ValidationError(_("Negative age: current year < DOB year!"))
                record.age = delta_year
            else:
                record.age = False
        pass

    # --- Các hàm ràng buộc (Constraints) ---
    @api.constrains('dob')
    def _check_dob(self):
        for record in self:
            if record.dob and record.dob.year < 1900:
                raise ValidationError(_("Invalid DOB!"))

    @api.depends('male_children_ids')
    def _compute_number_of_children(self):
        for record in self:
            record.number_of_children = len(record.male_children_ids)


    @api.constrains('father_id', 'mother_id')
    def _check_parents(self):
        """Validate parent relationships"""
        for record in self:
            # Kiểm tra cha != mẹ
            if record.father_id and record.mother_id:
                if record.father_id == record.mother_id:
                    raise ValidationError(_("Father and Mother cannot be the same animal!"))
            
            # Kiểm tra cha != record hiện tại
            if record.father_id:
                if record.father_id.id == record.id:
                    raise ValidationError(_("An animal cannot be its own father!"))
            
            # Kiểm tra mẹ != record hiện tại
            if record.mother_id:
                if record.mother_id.id == record.id:
                    raise ValidationError(_("An animal cannot be its own mother!"))

    @api.constrains('gender', 'female_children_ids', 'male_children_ids')
    def _check_gender_children_consistency(self):
        """Validate gender and children lists consistency"""
        for record in self:
            # Kiểm tra không đồng thời có cả female_children_ids và male_children_ids
            if record.female_children_ids and record.male_children_ids:
                raise ValidationError(_(
                    "An animal cannot have both female children list and male children list. "
                    "Please check the parent assignments."
                ))
            
            # Giới tính đực (male) không được phép có female_children_ids
            if record.gender == 'male' and record.female_children_ids:
                raise ValidationError(_(
                    "A male animal cannot have female children in the female_children_ids field. "
                    "Male animals should only have children in male_children_ids (as father)."
                ))
            
            # Giới tính cái (female) không được phép có male_children_ids
            if record.gender == 'female' and record.male_children_ids:
                raise ValidationError(_(
                    "A female animal cannot have male children in the male_children_ids field. "
                    "Female animals should only have children in female_children_ids (as mother)."
                ))

    # --- Các hàm thay đổi (Onchange Functions) ---
    @api.onchange('weight')
    def _update_weight_pound(self):
        self.weight_pound = self.weight * 2.204623

    @api.onchange('weight_pound')
    def _update_weight_kg(self):
        self.weight = self.weight_pound / 2.204623