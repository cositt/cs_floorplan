from lxml import etree

from .test_cs_floorplan import TestCsFloorplanBase


class TestFloorplanOverviewAction(TestCsFloorplanBase):

    def test_action_returns_client_action_with_residence_id(self):
        action = self.residence.action_view_floorplan_overview()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'cs_floorplan_overview')
        self.assertEqual(action['params']['residence_id'], self.residence.id)

    def test_overview_button_hidden_without_floors(self):
        empty_residence = self.env['cs.residence'].create({
            'name': 'Residencia Sin Plantas',
            'code': 'NOFLR',
        })
        view = empty_residence.get_view(
            view_id=self.env.ref('cs_resident.residence_view_form').id, view_type='form'
        )
        arch = etree.fromstring(view['arch'])
        buttons = arch.xpath("//button[@name='action_view_floorplan_overview']")
        self.assertTrue(buttons)
        self.assertEqual(buttons[0].get('invisible'), 'not id or floor_count == 0')
