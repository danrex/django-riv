from django.test import Client, TestCase

class BaseTestCase(TestCase):
	fixtures = ['initial_data.json',]

	def setUp(self):
		self.client = Client(HTTP_HOST='localhost:8000')

	def tearDown(self):
		pass

from resources import *
from serializers import *

