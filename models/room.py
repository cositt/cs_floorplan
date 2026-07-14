from odoo import _, api, fields, models
from odoo.exceptions import AccessError

LAYOUT_FIELDS = {'pos_x', 'pos_y', 'width', 'height', 'floor_id'}


class Room(models.Model):
    _inherit = 'cs.room'

    floor_id = fields.Many2one('cs.residence.floor', string='Planta (Plano)', ondelete='set null')
    pos_x = fields.Float(string='Posición X', default=20)
    pos_y = fields.Float(string='Posición Y', default=20)
    width = fields.Float(string='Ancho', default=120)
    height = fields.Float(string='Alto', default=90)

    def _check_floorplan_layout_access(self, vals):
        if not LAYOUT_FIELDS.intersection(vals):
            return
        if self.env.su or self.env.user.has_group('cs_floorplan.group_cs_floorplan_manager'):
            return
        raise AccessError(_('Solo un editor de plano puede mover, redimensionar o reasignar de planta las habitaciones.'))

    def write(self, vals):
        self._check_floorplan_layout_access(vals)
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_floorplan_layout_access(vals)
        return super().create(vals_list)
