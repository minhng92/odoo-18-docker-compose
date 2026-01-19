# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import ValidationError


class LdCourse(models.Model):
    _name = 'ld.course'
    _description = 'Training Course Master Data'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name asc'

    # ==================================================================================
    # 1. HEADER INFO
    # ==================================================================================
    name = fields.Char(
        string='Course Title',
        required=True,
        translate=True,
        tracking=True,
        help="The public name of the course visible to employees."
    )

    code = fields.Char(
        string='Course Code',
        required=True,
        copy=False,
        tracking=True,
        help="Unique identifier (e.g., SOFT-001) for integration and quick search."
    )

    active = fields.Boolean(
        default=True,
        help="If unchecked, the course is hidden (archived) but history is preserved."
    )

    # Link to ld_category
    category_id = fields.Many2one(
        comodel_name='ld.course.category',
        string='Category',
        required=True,
        tracking=True,
        group_expand='_read_group_category_ids',  # Allow Kanban grouping by category even if empty
        help="Classification of the course (e.g., Leadership, Technical)."
    )

    # ==================================================================================
    # 2. CONTENT & SYLLABUS
    # ==================================================================================
    description = fields.Html(
        string='Syllabus & Details',
        sanitize=True,
        help="Detailed course content, agenda, and learning objectives."
    )

    description_short = fields.Char(
        string='Short Description',
        size=150,
        help="Brief summary for Kanban cards or SEO meta description."
    )

    # ==================================================================================
    # 3. LOGISTICS
    # ==================================================================================
    duration = fields.Float(
        string='Duration (Hours)',
        default=1.0,
        help="Standard duration in hours. Used as default for new sessions."
    )

    delivery_method = fields.Selection(
        selection=[
            ('classroom', 'In-Person'),
            ('online', 'Online'),
            ('hybrid', 'Blended')
        ],
        string='Delivery Method',
        default='classroom',
        required=True,
        tracking=True
    )

    # ==================================================================================
    # 4. REQUIREMENTS & PREREQUISITES
    # ==================================================================================
    prerequisite_ids = fields.Many2many(
        comodel_name='ld.course',
        relation='ld_course_prereq_rel',
        column1='course_id',
        column2='prereq_id',
        string='Prerequisites',
        domain="[('id', '!=', id)]",  # Prevent selecting itself in UI
        help="Courses that must be completed before taking this course."
    )

    # ==================================================================================
    # 5. SKILL GAPS & OUTCOMES
    # ==================================================================================
    skill_outcome_ids = fields.One2many(
        comodel_name='ld.course.skill',
        inverse_name='course_id',
        string='Skill Outcomes',
        copy=True
    )

    # ==================================================================================
    # 6. ORGANIZATION & STATUS
    # ==================================================================================
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Course Manager',
        default=lambda self: self.env.user,
        tracking=True,
        help="Person responsible for the course content."
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('published', 'Published')
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help="Draft: Under construction. Published: Visible in Catalog."
    )

    # ==================================================================================
    # CONSTRAINTS
    # ==================================================================================
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'The Course Code must be unique!')
    ]

    @api.constrains('prerequisite_ids')
    def _check_prerequisites_recursion(self):
        """ Prevent circular dependencies (A needs B, B needs A) """
        if not self._check_m2m_recursion('prerequisite_ids'):
            raise ValidationError(_("Circular dependency detected in Prerequisites. You cannot make a course a prerequisite of itself."))

    @api.constrains('duration')
    def _check_positive_duration(self):
        for record in self:
            if record.duration < 0:
                raise ValidationError(_("Duration cannot be negative."))

    # ==================================================================================
    # CRUD OVERRIDES
    # ==================================================================================
    def copy(self, default=None):
        """ Override copy to prevent unique constraint error on 'code'. """
        default = default or {}
        if 'code' not in default:
            default['code'] = _("%s (Copy)") % self.code
        if 'name' not in default:
            default['name'] = _("%s (Copy)") % self.name
        return super(LdCourse, self).copy(default)

    # ==================================================================================
    # HELPER METHODS
    # ==================================================================================
    @api.model
    def _read_group_category_ids(self, categories, domain, order):
        """ Display all categories in Kanban view even if empty """
        category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    # ==================================================================================
    # WORKFLOW ACTIONS
    # ==================================================================================
    def action_publish(self):
        """ Transition: Draft -> Published """
        for record in self:
            # Optional: Add validation here (e.g., must have description)
            if not record.description:
                # Just a warning, or raise ValidationError if strict
                pass 
            record.write({'state': 'published'})

    def action_draft(self):
        """ Transition: Published -> Draft """
        self.write({'state': 'draft'})


class LdCourseSkill(models.Model):
    _name = 'ld.course.skill'
    _description = 'Course Skill Outcome'
    _rec_name = 'skill_id'

    course_id = fields.Many2one(
        comodel_name='ld.course',
        string='Course',
        ondelete='cascade',
        required=True
    )

    skill_type_id = fields.Many2one(
        comodel_name='hr.skill.type',
        string='Skill Type',
        required=True
    )

    skill_id = fields.Many2one(
        comodel_name='hr.skill',
        string='Skill',
        required=True,
        domain="[('skill_type_id', '=', skill_type_id)]"
    )

    skill_level_id = fields.Many2one(
        comodel_name='hr.skill.level',
        string='Target Level',
        required=True,
        domain="[('skill_type_id', '=', skill_type_id)]",
        help="The level the learner is expected to achieve."
    )

    @api.onchange('skill_type_id')
    def _onchange_skill_type_id(self):
        """ Clear dependent fields when Type changes to prevent invalid data """
        self.skill_id = False
        self.skill_level_id = False

    _sql_constraints = [
        ('unique_course_skill', 'UNIQUE(course_id, skill_id)', 'This skill is already defined for this course.')
    ]
