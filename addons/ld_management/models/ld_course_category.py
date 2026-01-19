# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LdCourseCategory(models.Model):
    _name = 'ld.course.category'
    _description = 'Course Category'
    _parent_store = True  # Optimized hierarchy handling
    _order = 'sequence, name'
    _rec_name = 'complete_name' # Show "Parent / Child" instead of just "Child"

    # ==================================================================================
    # 1. BASIC INFO
    # ==================================================================================
    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )

    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True,
        recursive=True,
        help="Full path of the category (e.g. Technical / Python / Basic)"
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order in lists and catalog."
    )

    color = fields.Integer(
        string='Color Index',
        help="Color tag for the Kanban view."
    )

    active = fields.Boolean(default=True)

    # ==================================================================================
    # 2. HIERARCHY
    # ==================================================================================
    parent_id = fields.Many2one(
        comodel_name='ld.course.category',
        string='Parent Category',
        index=True,
        ondelete='cascade'
    )

    parent_path = fields.Char(index=True, unaccent=False) # Required by _parent_store

    child_ids = fields.One2many(
        comodel_name='ld.course.category',
        inverse_name='parent_id',
        string='Sub-Categories'
    )

    # ==================================================================================
    # 3. STATISTICS
    # ==================================================================================
    course_count = fields.Integer(
        string='Course Count',
        compute='_compute_course_count',
        help="Number of courses belonging to this category."
    )

    # ==================================================================================
    # COMPUTE METHODS
    # ==================================================================================
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    def _compute_course_count(self):
        # We perform a read_group for performance optimization
        # Logic: We count courses directly linked to this category
        data = self.env['ld.course'].read_group(
            [('category_id', 'in', self.ids)], 
            ['category_id'], 
            ['category_id']
        )
        mapped_data = {d['category_id'][0]: d['category_id_count'] for d in data}
        for category in self:
            category.course_count = mapped_data.get(category.id, 0)

    # ==================================================================================
    # CONSTRAINTS
    # ==================================================================================
    @api.constrains('parent_id')
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive categories.'))
