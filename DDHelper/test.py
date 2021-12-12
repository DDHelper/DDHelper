from django.test import TestCase
from django.core.exceptions import BadRequest
from DDHelper.util import load_params

class load_params_Test(TestCase):
    def test_KeyError(self):
        with self.assertRaises(BadRequest):
            with load_params():
                raise KeyError
    def test_ValueError(self):
        with self.assertRaises(BadRequest):
            with load_params():
                raise ValueError('Testing ERROR')
