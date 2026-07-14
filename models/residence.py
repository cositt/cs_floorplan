from odoo import _, api, fields, models


class Residence(models.Model):
    _inherit = 'cs.residence'

    floor_ids = fields.One2many('cs.residence.floor', 'residence_id', string='Plantas')
    floor_count = fields.Integer(string='Nº Plantas', compute='_compute_floor_count')

    @api.depends('floor_ids')
    def _compute_floor_count(self):
        for residence in self:
            residence.floor_count = len(residence.floor_ids)

    def action_view_floors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plantas'),
            'res_model': 'cs.residence.floor',
            'view_mode': 'list,form',
            'domain': [('residence_id', '=', self.id)],
            'context': {'default_residence_id': self.id},
        }
