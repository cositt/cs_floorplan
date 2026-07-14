from odoo import api, fields, models


class ResidenceFloor(models.Model):
    _name = 'cs.residence.floor'
    _description = 'Planta de Residencia'
    _order = 'residence_id, sequence, name'

    name = fields.Char(string='Nombre de Planta', required=True)
    residence_id = fields.Many2one(
        'cs.residence',
        string='Residencia',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Secuencia', default=10)
    room_ids = fields.One2many('cs.room', 'floor_id', string='Habitaciones')
    room_count = fields.Integer(string='Nº Habitaciones', compute='_compute_room_count')

    @api.depends('room_ids')
    def _compute_room_count(self):
        for floor in self:
            floor.room_count = len(floor.room_ids)

    def action_print_floorplan(self):
        self.ensure_one()
        return self.env.ref('cs_floorplan.action_report_residence_floor').report_action(self)
