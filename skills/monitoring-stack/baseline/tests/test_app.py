import io
import unittest
from app import Application

class AppTests(unittest.TestCase):
    def test_existing_response_and_errors(self):
        app=Application()
        def request(path):
            status=[]
            data=b''.join(app({'PATH_INFO':path,'REQUEST_METHOD':'GET','wsgi.input':io.BytesIO()},lambda s,h:status.append(s)))
            return status[0],data
        self.assertEqual(request('/')[0],'200 OK')
        self.assertIn(b'hello',request('/')[1])
        self.assertEqual(request('/fail')[0],'503 Service Unavailable')
        self.assertEqual(request('/boom')[0],'500 Internal Server Error')
        self.assertEqual(request('/missing/123')[0],'404 Not Found')
        self.assertIn(b'__unmatched__',request('/metrics')[1])
        self.assertNotIn(b'/missing/123',request('/metrics')[1])
