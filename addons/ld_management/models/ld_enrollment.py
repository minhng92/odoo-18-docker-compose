# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LdEnrollment(models.Model):
    _name = 'ld.enrollment'
    _description = 'Training Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # ==================================================================================
    # 1. IDENTIFICATION & RELATIONS
    # ==================================================================================
    name = fields.Char(
        string='Enrollment ID',
        readonly=True,
        compute='_compute_name',
        store=True,
        help="Auto-generated name: [Employee] - [Session]"
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        tracking=True,
        ondelete='restrict'
    )

    session_id = fields.Many2one(
        comodel_name='ld.session',
        string='Training Session',
        required=True,
        tracking=True,
        ondelete='cascade',
        domain="[('state', 'in', ['confirmed', 'ongoing'])]" # Only allow enrollment in open sessions
    )

    course_id = fields.Many2one(
        related='session_id.course_id',
        string='Course',
        store=True,
        readonly=True
    )

    request_id = fields.Many2one(
        comodel_name='ld.training.request',
        string='Source Request',
        readonly=True,
        help="The training request that initiated this enrollment."
    )

    # ==================================================================================
    # 2. STATUS & ATTENDANCE
    # ==================================================================================
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('waitlist', 'Waitlisted'),
            ('confirmed', 'Confirmed'), # Seat reserved
            ('attended', 'Attended'),   # Finished classes, waiting for grading
            ('passed', 'Passed'),       # Final Success
            ('failed', 'Failed'),       # Final Failure
            ('cancel', 'Cancelled')
        ],
        string='Status',
        default='draft',
        tracking=True,
        group_expand='_expand_states',
        index=True
    )

    active = fields.Boolean(default=True)

    attendance_ids = fields.One2many(
        comodel_name='ld.enrollment.attendance',
        inverse_name='enrollment_id',
        string='Attendance Records'
    )

    # Attendance Summary
    attended_sessions_count = fields.Integer(
        string='Sessions Attended',
        compute='_compute_attendance_stats',
        store=True
    )
    
    is_attended = fields.Boolean(
        string='Attendance Qualified',
        compute='_compute_attendance_stats',
        store=True,
        help="True if the student attended enough sessions to qualify for grading."
    )

    # ==================================================================================
    # 3. EVALUATION & RESULTS (Level 2)
    # ==================================================================================
    score = fields.Float(string='Score Achieved', tracking=True)
    score_max = fields.Float(string='Max Score', default=100.0)
    
    grade = fields.Selection(
        selection=[('pass', 'Pass'), ('fail', 'Fail')],
        string='Final Grade',
        compute='_compute_grade',
        store=True,
        readonly=False, # Allow manual override
        tracking=True
    )

    completion_date = fields.Date(string='Completion Date', tracking=True)

    # ==================================================================================
    # 4. CERTIFICATION & FEEDBACK
    # ==================================================================================
    certificate_url = fields.Char(string='Certificate URL', readonly=True)
    
    # Link to Odoo Survey result (if online test is used)
    survey_input_id = fields.Many2one(
        comodel_name='survey.user_input',
        string='Test Result',
        readonly=True
    )

    has_badge = fields.Boolean(string='Badge Granted', default=False)

    # ==================================================================================
    # COMPUTE METHODS
    # ==================================================================================
    @api.depends('employee_id.name', 'session_id.name')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.session_id:
                record.name = f"{record.employee_id.name} - {record.session_id.name}"
            else:
                record.name = _("New Enrollment")

    @api.depends('attendance_ids', 'attendance_ids.state')
    def _compute_attendance_stats(self):
        for record in self:
            # Logic: Count 'present' records
            present_count = len(record.attendance_ids.filtered(lambda a: a.state == 'present'))
            record.attended_sessions_count = present_count
            
            # Simple Logic: Need > 0 attendance to be 'Attended'. 
            # Real Logic: Compare with session.min_attendance_percent (Future improvement)
            record.is_attended = present_count > 0

    @api.depends('score', 'score_max')
    def _compute_grade(self):
        """ Auto-calculate grade based on score threshold (e.g., 50%) """
        for record in self:
            if record.state in ['passed', 'failed']:
                continue # Don't overwrite if finalized
            
            if record.score_max > 0:
                percentage = (record.score / record.score_max) * 100
                # Assuming 50% is pass mark. Can be configured in ld.course later.
                if percentage >= 50:
                    record.grade = 'pass'
                else:
                    record.grade = 'fail'

    # ==================================================================================
    # CONSTRAINTS
    # ==================================================================================
    _sql_constraints = [
        ('unique_enrollment', 
         'UNIQUE(employee_id, session_id)', 
         'This employee is already enrolled in this session. Please check existing records.')
    ]

    @api.constrains('session_id')
    def _check_session_state(self):
        for record in self:
            if record.session_id.state in ['done', 'cancel']:
                raise ValidationError(_("Cannot enroll in a session that is Closed or Cancelled."))

    @api.constrains('employee_id', 'course_id')
    def _check_prerequisites(self):
        """
        Check if the employee has completed all prerequisite courses.
        Logic: Search for 'passed' enrollments in previous courses.
        """
        for record in self:
            prereqs = record.course_id.prerequisite_ids
            if not prereqs:
                continue

            # Find completed courses by this employee
            completed_enrollments = self.search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'passed'),
                ('course_id', 'in', prereqs.ids)
            ])
            completed_course_ids = completed_enrollments.mapped('course_id.id')

            # Identify missing prereqs
            missing = prereqs.filtered(lambda c: c.id not in completed_course_ids)
            if missing:
                missing_names = ", ".join(missing.mapped('name'))
                raise ValidationError(_("Prerequisites not met. You must complete the following courses first: %s") % missing_names)

    # ==================================================================================
    # WORKFLOW ACTIONS
    # ==================================================================================
    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_attended(self):
        """ Mark as attended, ready for grading """
        self.write({'state': 'attended'})

    def action_pass(self):
        """ Finalize as Passed -> Grant Skills """
        self.write({
            'state': 'passed',
            'completion_date': fields.Date.today()
        })
        self._grant_skills()

    def action_fail(self):
        self.write({'state': 'failed'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    # ==================================================================================
    # BUSINESS LOGIC
    # ==================================================================================
    def _grant_skills(self):
        """
        Add skill levels to employee profile based on Course outcomes.
        """
        for record in self:
            if not record.course_id.skill_outcome_ids:
                continue
                
            for outcome in record.course_id.skill_outcome_ids:
                # Logic: Check if employee already has skill. Update if level is higher.
                # This requires interaction with 'hr.employee.skill' model.
                # Implementation depends on HR Skills module API.
                pass 

    @api.model
    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]


class LdEnrollmentAttendance(models.Model):
    _name = 'ld.enrollment.attendance'
    _description = 'Detailed Attendance Record'

    enrollment_id = fields.Many2one('ld.enrollment', required=True, ondelete='cascade')
    date = fields.Date(default=fields.Date.today, required=True)
    state = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused')
    ], default='present', required=True)
    remarks = fields.Char()
