# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class CageUpdateWizard(models.TransientModel):
    _name = "zoo.cage.update.wizard"
    _description = "Update Cage for Animals"

    cage_id = fields.Many2one('zoo.cage', string='Cage', required=True, help='Select cage to assign to animals')

    def update_cage(self):
        """Update cage for selected animals"""
        # Get selected animal IDs from context
        animal_ids = self.env.context.get('active_ids', [])
        
        if not animal_ids:
            raise UserError(_("No animals selected!"))
        
        # Browse and update animals
        zoo_animals = self.env["zoo.animal"].browse(animal_ids)
        
        # Update cage_id for all selected animals
        zoo_animals.write({
            'cage_id': self.cage_id.id
        })
        
        # Log action
        _logger.info(f"Updated cage to '{self.cage_id.name}' for {len(zoo_animals)} animal(s)")
        
        # Return action to refresh the view
        return {'type': 'ir.actions.act_window_close'}
