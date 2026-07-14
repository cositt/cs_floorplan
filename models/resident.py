from odoo import _, api, models
from odoo.exceptions import ValidationError


class Resident(models.Model):
    _inherit = 'cs.resident'

    @api.constrains('room_id', 'state')
    def _check_floorplan_room_capacity(self):
        for resident in self:
            room = resident.room_id
            if not room or resident.state != 'activo':
                continue
            active_count = len(room.resident_ids.filtered(lambda r: r.state == 'activo'))
            if active_count > room.capacidad:
                raise ValidationError(_(
                    'La habitación %(room)s no tiene plazas libres (capacidad: %(cap)s).',
                    room=room.name,
                    cap=room.capacidad,
                ))
