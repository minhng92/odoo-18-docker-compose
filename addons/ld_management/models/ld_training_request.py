# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class LdTrainingRequest(models.Model):
    _name = 'ld.training.request'
    _description = 'Training Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # ==================================================================================
    # 1. IDENTIFICATION & SYSTEM FIELDS (Hard Readonly)
    # These fields are managed by the system and must not be edited manually by users.
    # ==================================================================================
    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Unique identifier for the training request (e.g., TR/2024/001)."
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('submitted', 'To Approve'),
            ('approved', 'Approved'),    # Approved by Manager, pending L&D action
            ('done', 'Enrolled'),        # Officially enrolled in a session
            ('waitlist', 'Waitlisted'),  # Approved but session is full
            ('rejected', 'Rejected'),
            ('cancel', 'Cancelled')
        ],
        string='Status',
        default='draft',
        readonly=True,  # Protected state machine
        tracking=True,
        group_expand='_expand_states',  # Enables drag-and-drop in Kanban
        index=True
    )

    active = fields.Boolean(default=True, help="Archive requests instead of deleting them.")

    # ==================================================================================
    # 2. REQUESTER INFO (Hybrid Readonly)
    # Managed via XML: readonly="state != 'draft'"
    # ==================================================================================
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True,
        help="The employee requesting the training."
    )

    # Related fields are Readonly=True by default in logic (safe)
    department_id = fields.Many2one(
        related='employee_id.department_id',
        store=True,
        string='Department',
        readonly=True
    )

    job_id = fields.Many2one(
        related='employee_id.job_id',
        store=True,
        string='Job Position',
        readonly=True
    )

    line_manager_id = fields.Many2one(
        related='employee_id.parent_id.user_id',
        store=True,
        string='Line Manager',
        readonly=True,
        help="The user responsible for approving this request (derived from HR Hierarchy)."
    )

    # ==================================================================================
    # 3. TRAINING DETAILS (Hybrid Readonly)
    # Managed via XML: readonly="state != 'draft'"
    # ==================================================================================
    course_id = fields.Many2one(
        comodel_name='ld.course',
        string='Course',
        required=True,
        domain="[('state', '=', 'published')]", # Activate when ld.course is ready
        tracking=True
    )

    suggested_session_id = fields.Many2one(
        comodel_name='ld.session',
        string='Suggested Session',
        # domain="[('course_id', '=', course_id), ('state', '!=', 'done')]", # Activate when ld.session is ready
        help="Optional: The specific session the employee wants to join."
    )

    justification = fields.Text(
        string='Justification',
        required=True,
        tracking=True,
        help="Gap Analysis: Why is this training necessary?"
    )

    skill_gap_id = fields.Many2one(
        comodel_name='hr.skill',
        string='Target Skill',
        help="The specific skill that needs improvement."
    )

    urgency = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'Urgent'),
            ('2', 'Critical')
        ],
        string='Urgency',
        default='0',
        tracking=True
    )

    # ==================================================================================
    # 4. PROCESSING RESULTS (Hard Readonly)
    # Updated automatically by system actions.
    # ==================================================================================
    enrollment_id = fields.Many2one(
        comodel_name='ld.enrollment',
        string='Enrollment Record',
        readonly=True,
        copy=False
    )

    enrollment_status = fields.Char(
        string='Enrollment Status',
        compute='_compute_enrollment_status',
        store=False,  # Compute on the fly to reflect real-time status
        help="Real-time status derived from the Enrollment record."
    )

    waitlist_position = fields.Integer(
        string='Waitlist Position',
        readonly=True,
        copy=False,
        help="Position in the waiting list if the session is full."
    )

    rejection_reason = fields.Text(
        string='Rejection Reason',
        readonly=True,
        tracking=True,
        help="Reason provided by the Manager when rejecting the request."
    )

    manager_approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
        copy=False,
        help="The date and time when the Line Manager approved this request."
    )

    # ==================================================================================
    # ONCHANGE LOGIC
    # ==================================================================================
    @api.onchange('course_id')
    def _onchange_course_id(self):
        """Reset suggested session if course changes to prevent data mismatch."""
        if self.course_id:
            self.suggested_session_id = False

    # ==================================================================================
    # COMPUTE METHODS
    # ==================================================================================
    @api.depends('enrollment_id', 'enrollment_id.state')
    def _compute_enrollment_status(self):
        """
        Fetches the human-readable state of the related enrollment.
        """
        for record in self:
            if record.enrollment_id:
                # We use dict(selection) to get the label (e.g., 'Completed') instead of key ('done')
                # Handling case where ld.enrollment might not be fully defined yet
                try:
                    selection = record.enrollment_id._fields['state'].selection
                    if callable(selection):
                        selection = selection(record.enrollment_id)
                    state_label = dict(selection).get(record.enrollment_id.state)
                    record.enrollment_status = state_label or record.enrollment_id.state
                except (AttributeError, KeyError):
                    record.enrollment_status = str(record.enrollment_id.state)
            else:
                record.enrollment_status = _('Not Enrolled')

    # ==================================================================================
    # ORM METHODS
    # ==================================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """ Assign sequence on creation """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                # Gọi sequence dựa trên field 'code' trong file XML
                vals['name'] = self.env['ir.sequence'].next_by_code('ld.training.request') or _('New')
        return super(LdTrainingRequest, self).create(vals_list)

    # ==================================================================================
    # CONSTRAINTS
    # ==================================================================================
    @api.constrains('employee_id', 'course_id', 'state')
    def _check_duplicate_request(self):
        """
        Business Rule: Prevent spamming. 
        An employee cannot have concurrent active requests for the same course.
        """
        for record in self:
            # Skip check if the request is already finished or cancelled
            if record.state in ['done', 'cancel', 'rejected']:
                continue

            domain = [
                ('employee_id', '=', record.employee_id.id),
                ('course_id', '=', record.course_id.id),
                ('state', 'not in', ['done', 'cancel', 'rejected']), # Check all active states
                ('id', '!=', record.id)  # Exclude self
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(_("You already have an active request for this course. Please complete or cancel it before creating a new one."))

    # ==================================================================================
    # WORKFLOW ACTIONS
    # ==================================================================================
    def action_submit(self):
        """ Transition: Draft -> To Approve """
        self.ensure_one()
        if not self.justification:
            raise UserError(_("Please provide a justification before submitting."))
        self.write({'state': 'submitted'})
        # Optional: Notify Line Manager
        # self._notify_line_manager()

    def action_manager_approve(self):
        """
        Transition: To Approve -> Approved/Done/Waitlist
        Logic:
        1. Security Check: Only Line Manager or L&D Admin.
        2. Session Allocation: Auto-enroll if session is selected.
        """
        self.ensure_one()

        # 1. Validation: Check Permissions
        # Logic: Current User must be the Line Manager OR have 'Manager' group.
        is_line_manager = self.env.user == self.line_manager_id
        is_admin = self.env.user.has_group('ld_management.group_ld_manager')

        # Policy: Requester cannot approve their own request unless they are the Admin.
        if self.env.user.employee_id == self.employee_id and not is_admin:
            raise UserError(_("You cannot approve your own training request."))

        if not is_line_manager and not is_admin:
            raise UserError(_("Only the Line Manager (%s) or L&D Managers can approve this request.") % self.line_manager_id.name)

        # 2. Process Approval
        if self.suggested_session_id:
            # If session is selected, try to enroll immediately
            self._process_auto_enrollment(self.suggested_session_id)

            # Update Audit Date after enrollment logic (which handles state)
            self.write({'manager_approval_date': fields.Datetime.now()})
        else:
            # Generic Approval (No session selected)
            self.write({
                'state': 'approved',
                'manager_approval_date': fields.Datetime.now()
            })

            # self.message_post(body=_("Request approved. Waiting for session assignment."))

    def _process_auto_enrollment(self, session):
        """
        Private Logic: Handle Capacity and Enrollment creation.
        """
        Enrollment = self.env['ld.enrollment']

        # 1. Check Capacity
        # Safety check: Handle case where 'seats_available' doesn't exist yet in ld.session
        seats_available = getattr(session, 'seats_available', 999)

        if seats_available > 0:
            # Scenario A: Confirmed Enrollment
            enrollment = Enrollment.create({
                'employee_id': self.employee_id.id,
                'session_id': session.id,
                'request_id': self.id,
                'state': 'confirmed'
            })
            self.write({
                'state': 'done',
                'enrollment_id': enrollment.id
            })
            self.message_post(body=_("System auto-enrolled employee into session: %s") % session.name)
        else:
            # Scenario B: Waitlist
            # Calculate position
            current_waitlist_count = Enrollment.search_count([
                ('session_id', '=', session.id),
                ('state', '=', 'waitlist')
            ])
            position = current_waitlist_count + 1

            enrollment = Enrollment.create({
                'employee_id': self.employee_id.id,
                'session_id': session.id,
                'request_id': self.id,
                'state': 'waitlist'
            })
            self.write({
                'state': 'waitlist',
                'enrollment_id': enrollment.id,
                'waitlist_position': position
            })
            self.message_post(body=_("Session is full. Added to Waitlist at position #%s.") % position)

    def action_reject(self):
        """
        Opens the Rejection Wizard instead of immediate rejection.
        """
        self.ensure_one()

        # 1. Pre-check permissions to fail fast before opening wizard
        is_line_manager = self.env.user == self.line_manager_id
        is_admin = self.env.user.has_group('ld_management.group_ld_manager')

        if not is_line_manager and not is_admin:
            raise UserError(_("You do not have permission to reject this request."))

        # 2. Open Wizard
        return {
            'name': _('Reject Training Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'ld.training.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reason': '',  # Optional: Pre-fill
                'active_id': self.id,
                'active_model': 'ld.training.request'
            }
        }

    def action_reset_to_draft(self):
        """
        Allows the Requester or Officer to reset the request to Draft.
        Useful when the user wants to change the course or session after approval/waitlisting.
        """
        for record in self:
            # 1. Guard: Prevent resetting if already successfully enrolled (Done)
            # 'done' means the seat is confirmed and possibly paid for. Must Cancel instead.
            if record.state == 'done':
                raise UserError(_("You cannot reset an enrolled request. Please cancel it first."))

            # 2. Cleanup: Remove existing Enrollment (Waitlist or Reservation)
            if record.enrollment_id:
                # We unlink (delete) the enrollment to free up the session capacity/queue immediately.
                # Assuming standard Odoo 'unlink' behavior handles cascading or we rely on SQL constraints.
                record.enrollment_id.unlink()

            # 3. Reset: Clear all approval and processing data
            record.write({
                'state': 'draft',
                'manager_approval_date': False,  # Clear audit date
                'rejection_reason': False,       # Clear previous rejection notes
                'waitlist_position': 0,          # Reset queue position
                'enrollment_id': False           # Unlink relation
            })

            # Log the action for transparency
            record.message_post(body=_("Request reset to Draft. Previous approvals and waitlist positions have been cleared."))

    def action_cancel(self):
        """ Transition: -> Cancelled (By User) """
        for record in self:
            if record.state == 'done':
                raise UserError(_("You cannot cancel a request that is already enrolled. Please contact L&D."))
            record.write({'state': 'cancel'})

    # ==================================================================================
    # HELPER METHODS
    # ==================================================================================
    @api.model
    def _expand_states(self, states, domain, order):
        """
        Enable Kanban View to show all columns (states) even if they are empty.
        Linked via: state = fields.Selection(..., group_expand='_expand_states')
        """
        # Return all keys from the selection field definition
        return [key for key, val in type(self).state.selection]
