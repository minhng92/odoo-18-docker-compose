from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LdRoom(models.Model):
    """
    Master Data for Training Locations/Rooms.
    Managed via Configuration menu.
    """
    _name = 'ld.room'
    _description = 'Training Room / Location'
    _order = 'name asc'

    name = fields.Char(string='Room Name', required=True)
    capacity = fields.Integer(string='Capacity (Seats)', default=20, help="Max number of students.")
    address = fields.Char(string='Address/Location', help="Building, Floor, or URL if online.")

    # Simple check to prevent double booking is handled in Session model logic
