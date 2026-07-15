from lxml import etree

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase


class TestCsFloorplanBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.residence = cls.env['cs.residence'].create({
            'name': 'Residencia Test Plano',
            'code': 'TPL',
        })
        cls.floor = cls.env['cs.residence.floor'].create({
            'name': 'Planta 1',
            'residence_id': cls.residence.id,
        })
        cls.room = cls.env['cs.room'].create({
            'name': '101',
            'residence_id': cls.residence.id,
            'tipo': 'individual',
            'capacidad': 1,
            'floor_id': cls.floor.id,
        })
        cls.manager_group = cls.env.ref('cs_floorplan.group_cs_floorplan_manager')
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Editor Plano Test',
            'login': 'floorplan_manager_test',
            'group_ids': [(6, 0, (cls.env.ref('base.group_user') + cls.manager_group).ids)],
        })
        cls.plain_user = cls.env['res.users'].create({
            'name': 'Usuario Normal Test',
            'login': 'floorplan_plain_test',
            'group_ids': [(6, 0, cls.env.ref('base.group_user').ids)],
        })

    def _make_resident(self, **kwargs):
        defaults = {
            'name': 'Residente Test Plano',
            'dni': '11111111A',
            'fecha_nacimiento': '1950-01-01',
            'residence_id': self.residence.id,
        }
        defaults.update(kwargs)
        return self.env['cs.resident'].create(defaults)


class TestResidenceFloor(TestCsFloorplanBase):

    def test_floor_linked_to_residence(self):
        self.assertEqual(self.floor.residence_id, self.residence)
        self.assertIn(self.floor, self.residence.floor_ids)

    def test_residence_floor_count(self):
        self.assertEqual(self.residence.floor_count, 1)
        self.env['cs.residence.floor'].create({
            'name': 'Planta 2',
            'residence_id': self.residence.id,
        })
        self.assertEqual(self.residence.floor_count, 2)

    def test_floor_room_count(self):
        self.assertEqual(self.floor.room_count, 1)


class TestRoomLayoutFields(TestCsFloorplanBase):

    def test_room_default_position(self):
        room = self.env['cs.room'].create({
            'name': '102',
            'residence_id': self.residence.id,
            'tipo': 'individual',
        })
        self.assertEqual(room.pos_x, 20)
        self.assertEqual(room.pos_y, 20)
        self.assertEqual(room.width, 120)
        self.assertEqual(room.height, 90)
        self.assertFalse(room.floor_id)

    def test_manager_can_reposition_room(self):
        self.room.with_user(self.manager_user).write({'pos_x': 50, 'pos_y': 60})
        self.assertEqual(self.room.pos_x, 50)
        self.assertEqual(self.room.pos_y, 60)

    def test_plain_user_cannot_reposition_room(self):
        with self.assertRaises(AccessError):
            self.room.with_user(self.plain_user).write({'pos_x': 999})

    def test_plain_user_can_still_edit_non_layout_fields(self):
        self.room.with_user(self.plain_user).write({'notas': 'nota libre'})
        self.assertEqual(self.room.notas, 'nota libre')

    def test_plain_user_create_without_layout_fields_ok(self):
        room = self.env['cs.room'].with_user(self.plain_user).create({
            'name': '103',
            'residence_id': self.residence.id,
            'tipo': 'individual',
        })
        self.assertTrue(room)

    def test_plain_user_create_with_layout_field_blocked(self):
        with self.assertRaises(AccessError):
            self.env['cs.room'].with_user(self.plain_user).create({
                'name': '104',
                'residence_id': self.residence.id,
                'tipo': 'individual',
                'floor_id': self.floor.id,
            })


class TestRoomFormFloorField(TestCsFloorplanBase):
    """La habitación se crea desde el menú Centro de Salud (cs_resident.room_view_form).
    Ese formulario debe exponer floor_id para poder asignar planta ahí mismo,
    si no la habitación nunca aparece en el plano (canvas filtra por floor_id)."""

    def _get_room_form_arch(self, user):
        view = self.env['cs.room'].with_user(user).get_view(
            view_id=self.env.ref('cs_resident.room_view_form').id, view_type='form'
        )
        return etree.fromstring(view['arch'])

    def test_room_form_exposes_floor_field(self):
        arch = self._get_room_form_arch(self.manager_user)
        self.assertTrue(arch.xpath("//field[@name='floor_id']"))

    def test_manager_can_edit_floor_field_from_room_form(self):
        arch = self._get_room_form_arch(self.manager_user)
        fields = arch.xpath("//field[@name='floor_id']")
        self.assertTrue(fields)
        self.assertIsNone(fields[0].get('readonly'))

    def test_plain_user_sees_floor_field_readonly(self):
        arch = self._get_room_form_arch(self.plain_user)
        fields = arch.xpath("//field[@name='floor_id']")
        self.assertTrue(fields)
        self.assertEqual(fields[0].get('readonly'), '1')

    def test_room_list_exposes_floor_field(self):
        view = self.env['cs.room'].get_view(
            view_id=self.env.ref('cs_resident.room_view_list').id, view_type='list'
        )
        arch = etree.fromstring(view['arch'])
        self.assertTrue(arch.xpath("//field[@name='floor_id']"))

    def test_manager_sets_floor_from_room_form_and_room_shows_on_canvas(self):
        room = self.env['cs.room'].create({
            'name': '105',
            'residence_id': self.residence.id,
            'tipo': 'individual',
        })
        self.assertFalse(room.floor_id)
        room.with_user(self.manager_user).write({'floor_id': self.floor.id})
        self.assertIn(room, self.floor.room_ids)

    def test_residence_form_room_list_exposes_floor_field(self):
        """La lista de habitaciones embebida en la ficha de Residencia (uso diario)
        tiene su propio arch hardcodeado en cs_resident, no reutiliza room_view_list."""
        view = self.env['cs.residence'].get_view(
            view_id=self.env.ref('cs_resident.residence_view_form').id, view_type='form'
        )
        arch = etree.fromstring(view['arch'])
        room_list_fields = arch.xpath("//field[@name='room_ids']/list/field[@name='floor_id']")
        self.assertTrue(room_list_fields)

    def test_residence_form_still_has_floors_smart_button(self):
        """Regresión: hubo una colisión de xmlid entre dos vistas que hered
        residence_view_form y una pisó a la otra, borrando el botón 'Plantas'."""
        view = self.env['cs.residence'].get_view(
            view_id=self.env.ref('cs_resident.residence_view_form').id, view_type='form'
        )
        arch = etree.fromstring(view['arch'])
        self.assertTrue(arch.xpath("//button[@name='action_view_floors']"))

    def test_residence_form_room_list_readonly_for_plain_user(self):
        view = self.env['cs.residence'].with_user(self.plain_user).get_view(
            view_id=self.env.ref('cs_resident.residence_view_form').id, view_type='form'
        )
        arch = etree.fromstring(view['arch'])
        room_list_fields = arch.xpath("//field[@name='room_ids']/list/field[@name='floor_id']")
        self.assertTrue(room_list_fields)
        self.assertEqual(room_list_fields[0].get('readonly'), '1')


class TestResidentCapacity(TestCsFloorplanBase):

    def test_capacity_respected(self):
        self._make_resident(dni='22222222B', room_id=self.room.id)
        second = self._make_resident(dni='33333333C')
        with self.assertRaises(ValidationError):
            second.write({'room_id': self.room.id})

    def test_non_active_resident_does_not_count(self):
        self._make_resident(dni='44444444D', room_id=self.room.id)
        second = self._make_resident(dni='55555555E', state='baja')
        second.write({'room_id': self.room.id})
        self.assertEqual(second.room_id, self.room)


class TestFloorplanReport(TestCsFloorplanBase):

    def test_report_renders(self):
        html, report_type = self.env['ir.actions.report']._render_qweb_html(
            'cs_floorplan.report_residence_floor_document', self.floor.ids
        )
        self.assertIn(b'101', html)
        self.assertEqual(report_type, 'html')
