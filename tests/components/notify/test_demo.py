"""The tests for the notify demo platform."""
import unittest

from homeassistant.bootstrap import setup_component
import homeassistant.components.notify as notify
from homeassistant.components.notify import demo
from homeassistant.helpers import script

from tests.common import get_test_home_assistant


class TestNotifyDemo(unittest.TestCase):
    """Test the demo notify."""

    def setUp(self):  # pylint: disable=invalid-name
        """Setup things to be run when tests are started."""
        self.hass = get_test_home_assistant()
        self.assertTrue(setup_component(self.hass, notify.DOMAIN, {
            'notify': {
                'platform': 'demo'
            }
        }))
        self.events = []
        self.calls = []

        def record_event(event):
            """Record event to send notification."""
            self.events.append(event)

        self.hass.bus.listen(demo.EVENT_NOTIFY, record_event)

    def tearDown(self):  # pylint: disable=invalid-name
        """"Stop down everything that was started."""
        self.hass.stop()

    def record_calls(self, *args):
        """Helper for recording calls."""
        self.calls.append(args)

    def test_sending_none_message(self):
        """Test send with None as message."""
        notify.send_message(self.hass, None)
        self.hass.block_till_done()
        self.assertTrue(len(self.events) == 0)

    def test_sending_templated_message(self):
        """Send a templated message."""
        self.hass.states.set('sensor.temperature', 10)
        notify.send_message(self.hass, '{{ states.sensor.temperature.state }}',
                            '{{ states.sensor.temperature.name }}')
        self.hass.block_till_done()
        last_event = self.events[-1]
        self.assertEqual(last_event.data[notify.ATTR_TITLE], 'temperature')
        self.assertEqual(last_event.data[notify.ATTR_MESSAGE], '10')

    def test_method_forwards_correct_data(self):
        """Test that all data from the service gets forwarded to service."""
        notify.send_message(self.hass, 'my message', 'my title',
                            {'hello': 'world'})
        self.hass.block_till_done()
        self.assertTrue(len(self.events) == 1)
        data = self.events[0].data
        assert {
            'message': 'my message',
            'title': 'my title',
            'data': {'hello': 'world'}
        } == data

    def test_calling_notify_from_script_loaded_from_yaml_without_title(self):
        """Test if we can call a notify from a script."""
        conf = {
            'service': 'notify.notify',
            'data': {
                'data': {
                    'push': {
                        'sound':
                        'US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav'
                    }
                }
            },
            'data_template': {'message': 'Test 123 {{ 2 + 2 }}\n'},
        }

        script.call_from_config(self.hass, conf)
        self.hass.block_till_done()
        self.assertTrue(len(self.events) == 1)
        assert {
            'message': 'Test 123 4',
            'data': {
                'push': {
                    'sound':
                    'US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav'}}
        } == self.events[0].data

    def test_calling_notify_from_script_loaded_from_yaml_with_title(self):
        """Test if we can call a notify from a script."""
        conf = {
            'service': 'notify.notify',
            'data': {
                'data': {
                    'push': {
                        'sound':
                        'US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav'
                    }
                }
            },
            'data_template': {
                'message': 'Test 123 {{ 2 + 2 }}\n',
                'title': 'Test'
            }
        }

        script.call_from_config(self.hass, conf)
        self.hass.pool.block_till_done()
        self.assertTrue(len(self.events) == 1)
        assert {
            'message': 'Test 123 4',
            'title': 'Test',
            'data': {
                'push': {
                    'sound':
                    'US-EN-Morgan-Freeman-Roommate-Is-Arriving.wav'}}
        } == self.events[0].data

    def test_targets_are_services(self):
        """Test that all targets are exposed as individual services."""
        self.assertIsNotNone(self.hass.services.has_service("notify", "demo"))
        service = "demo_test_target_name"
        self.assertIsNotNone(self.hass.services.has_service("notify", service))

    def test_messages_to_targets_route(self):
        """Test message routing to specific target services."""
        self.hass.bus.listen_once("notify", self.record_calls)

        self.hass.services.call("notify", "demo_test_target_name",
                                {'message': 'my message',
                                 'title': 'my title',
                                 'data': {'hello': 'world'}})

        self.hass.block_till_done()

        data = self.calls[0][0].data

        assert {
            'message': 'my message',
            'target': ['test target id'],
            'title': 'my title',
            'data': {'hello': 'world'}
        } == data
