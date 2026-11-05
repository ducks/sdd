import unittest
import handler

class HandlerTests(unittest.TestCase):
    def test_expected_result(self):
        self.assertEqual(handler.prepare({'message':'hello'},1),{'message':'hello'})
