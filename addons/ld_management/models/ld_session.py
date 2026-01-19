# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LdSession(models.Model):
    _name = 'ld.session'
    _description = 'Training Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc'
    _rec_name = 'name'

    # ==================================================================================
    # 1. IDENTIFICATION
    # ==================================================================================
    name = fields.Char(
        string='Session Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Unique Sequence ID (e.g., SES/2024/00001)."
    )

    course_id = fields.Many2one(
        comodel_name='ld.course',
        string='Course',
        required=True,
        ondelete='restrict',
        tracking=True
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('ongoing', 'In Progress'),
            ('done', 'Completed'),
            ('cancel', 'Cancelled')
        ],
        string='Status',
        default='draft',
        tracking=True,
        group_expand='_expand_states',
        index=True
    )

    active = fields.Boolean(default=True)

    # ==================================================================================
    # 2. LOGISTICS
    # ==================================================================================
    instructor_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Instructor',
        required=True,
        tracking=True
    )

    location_id = fields.Many2one(
        comodel_name='ld.room',
        string='Training Room',
        tracking=True
    )

    # Related field to easily filter sessions by current user in Search View
    instructor_user_id = fields.Many2one(
        related='instructor_id.user_id',
        store=True,
        readonly=True,
        string="Instructor User"
    )

    delivery_method = fields.Selection(
        related='course_id.delivery_method',
        store=True,
        readonly=True
    )

    meeting_url = fields.Char(string='Meeting URL')

    # ==================================================================================
    # 3. SCHEDULING
    # ==================================================================================
    start_datetime = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True,
        default=fields.Datetime.now
    )

    end_datetime = fields.Datetime(
        string='End Date',
        required=True,
        tracking=True
    )

    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
        readonly=True
    )

    # ==================================================================================
    # 4. CAPACITY & ENROLLMENTS
    # ==================================================================================
    min_seats = fields.Integer(string='Min Participants', default=1)
    max_seats = fields.Integer(string='Max Capacity', default=20)

    enrollment_ids = fields.One2many(
        comodel_name='ld.enrollment',
        inverse_name='session_id',
        string='Enrollments'
    )

    seats_available = fields.Integer(
        string='Available Seats',
        compute='_compute_seats',
        store=True
    )

    waitlist_count = fields.Integer(
        string='Waitlist Size',
        compute='_compute_seats',
        store=True
    )

    enrollment_count = fields.Integer(
        string='Confirmed Attendees',
        compute='_compute_seats',
        store=True
    )

    # ==================================================================================
    # 5. EVALUATION
    # ==================================================================================
    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Feedback Form',
        domain="[('survey_type', '=', 'live_session')]"
    )

    # ==================================================================================
    # COMPUTE METHODS
    # ==================================================================================
    @api.depends('name', 'course_id.name')
    def _compute_display_name(self):
        """ 
        Custom Display Name: [Code] Course Name 
        E.g., [SES/2024/001] Excel Advanced
        """
        for record in self:
            if record.course_id and record.name != _('New'):
                record.display_name = f"[{record.name}] {record.course_id.name}"
            else:
                record.display_name = record.name or _('New')

    @api.depends('start_datetime', 'end_datetime')
    def _compute_duration(self):
        for record in self:
            if record.start_datetime and record.end_datetime:
                delta = record.end_datetime - record.start_datetime
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0

    @api.depends('max_seats', 'enrollment_ids', 'enrollment_ids.state')
    def _compute_seats(self):
        for record in self:
            # Logic: Count occupied seats (Confirmed, Attended, Passed, Failed)
            # We assume these states mean the seat is taken.
            confirmed = record.enrollment_ids.filtered(
                lambda e: e.state in ['confirmed', 'attended', 'passed', 'failed']
            )
            # Waitlist does NOT consume a seat capacity
            waitlisted = record.enrollment_ids.filtered(
                lambda e: e.state == 'waitlist'
            )

            record.enrollment_count = len(confirmed)
            record.seats_available = record.max_seats - len(confirmed)
            record.waitlist_count = len(waitlisted)

    # ==================================================================================
    # CRUD OVERRIDES (SEQUENCE)
    # ==================================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """ Generate Sequence ID on creation """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ld.session') or _('New')
        return super(LdSession, self).create(vals_list)

    # ==================================================================================
    # CONSTRAINTS
    # ==================================================================================
    @api.constrains('start_datetime', 'end_datetime')
    def _check_datetime_validity(self):
        for record in self:
            if record.start_datetime and record.end_datetime:
                if record.start_datetime >= record.end_datetime:
                    raise ValidationError(_("End Date must be after Start Date."))

    @api.constrains('instructor_id', 'start_datetime', 'end_datetime')
    def _check_instructor_availability(self):
        for record in self:
            domain = [
                ('instructor_id', '=', record.instructor_id.id),
                ('start_datetime', '<', record.end_datetime),
                ('end_datetime', '>', record.start_datetime),
                ('id', '!=', record.id),
                ('state', '!=', 'cancel')
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("Instructor %s is already booked for another session during this time.") % record.instructor_id.name)

    @api.constrains('location_id', 'start_datetime', 'end_datetime')
    def _check_location_availability(self):
        for record in self:
            if not record.location_id:
                continue
            domain = [
                ('location_id', '=', record.location_id.id),
                ('start_datetime', '<', record.end_datetime),
                ('end_datetime', '>', record.start_datetime),
                ('id', '!=', record.id),
                ('state', '!=', 'cancel')
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("Room %s is already booked during this time.") % record.location_id.name)

    # ==================================================================================
    # SMART BUTTON ACTIONS
    # ==================================================================================
    def action_view_enrollments(self):
        """
        Open the list of enrollments for this specific session.
        Triggered by the 'Attendees' smart button in the view.
        """
        self.ensure_one()
        return {
            'name': _('Attendees'),
            'type': 'ir.actions.act_window',
            'res_model': 'ld.enrollment',
            'view_mode': 'list,form',
            'domain': [('session_id', '=', self.id)],
            # Context ensures that if we create a new enrollment from this list,
            # the session_id is auto-filled.
            'context': {'default_session_id': self.id}
        }

    # ==================================================================================
    # WORKFLOW ACTIONS
    # ==================================================================================
    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirmed'})

    def action_ongoing(self):
        self.write({'state': 'ongoing'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    # ==================================================================================
    # HELPER
    # ==================================================================================
    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]
