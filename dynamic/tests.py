from django.test import TestCase
from . import bili_api


class ApiTest(TestCase):
    def test_api(self):
        user_profile = bili_api.user_profile(8401607)
        self.assertEqual(user_profile['code'], 0)
        self.assertEqual(user_profile['data']['mid'], 8401607)

        dynamic_history = bili_api.space_history(8401607, offset_dynamic_id=575349833245683072)
        self.assertEqual(dynamic_history['code'], 0)
        self.assertEqual(dynamic_history['data']['cards'][0]['desc']['uid'], 8401607)
        self.assertEqual(dynamic_history['data']['cards'][0]['desc']['dynamic_id'], 574365641487852129)
