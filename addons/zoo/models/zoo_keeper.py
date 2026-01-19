from odoo import models, fields, api

# ---------------------------------------------------------
# 1. MAIN MODEL: KEEPER (Inherit from HR Employee)
# ---------------------------------------------------------
class ZooKeeper(models.Model):
    _inherit = 'hr.employee'
    _description = 'Zoo Keeper Management'

    # flag để phân biệt Employee nào là Zoo Keepers
    is_zoo_keeper = fields.Boolean(string='Is Zoo Keeper',
        default=False)

    # Quan hệ với class con: Speciality (Many2many vì có thể share giữa nhiều keepers)
    speciality_ids = fields.Many2many(
        comodel_name='zoo.keeper.speciality',
        relation='zoo_keeper_speciality_rel',
        column1='employee_id',
        column2='speciality_id',
        string='Specialities',
        help='Species or families this keeper specializes in.')

    # Quan hệ với class con: Certification (One2many vì mỗi cert là unique)
    certification_ids = fields.One2many(
        comodel_name='zoo.keeper.certification',
        inverse_name='employee_id',
        string='Certifications',
        help='Certifications this keeper has.')
    
# ---------------------------------------------------------
# 2. SATELLITE MODELS (Master Data)
# ---------------------------------------------------------

class ZooKeeperSpeciality(models.Model):
    _name = 'zoo.keeper.speciality'
    _description = 'Zoo Keeper Speciality'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name',
        required=True)

    description = fields.Text(string='Description')

    # Quan hệ ngược: Many2many với hr.employee
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='zoo_keeper_speciality_rel',
        column1='speciality_id',
        column2='employee_id',
        string='Keepers',
        help='Keepers who have this speciality')

class ZooKeeperCertification(models.Model):
    _name = 'zoo.keeper.certification'
    _description = 'Zoo Keeper Certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Tạo số chứng chỉ
    certificate_code = fields.Char(
        string='Certificate Code',
        required=True,
        copy=False,  # Không copy khi duplicate
        help='Unique certificate number')

    name = fields.Char(string='Name',
        required=True)

    description = fields.Text(string='Description')
    
    # Link ngược về Employee
    employee_id = fields.Many2one(comodel_name='hr.employee',
        string='Keeper',
        required=True,
        ondelete='cascade')
    
    issue_date = fields.Date(string='Issue Date')

    expiry_date = fields.Date(string='Expiry Date')

    # File scan chứng chỉ
    attachment = fields.Binary(string='Certificate Document')

    # Computed field để cảnh báo hết hạn
    is_expired = fields.Boolean(compute='_compute_is_expired',
        string='Expired Date')

    # Computed field để cảnh báo hết hạn
    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for record in self:
            if record.expiry_date and record.expiry_date < today:
                record.is_expired = True
            else:
                record.is_expired = False

    # SQL Constraint để đảm bảo Certificate code là unique
    _sql_constraints = [
        ('certificate_code_unique', 
         'UNIQUE(certificate_code)', 
         'Certificate Code must be unique!')
    ]