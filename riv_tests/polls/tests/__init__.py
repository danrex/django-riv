from django.test import Client, TestCase
from django.contrib.auth.models import User

class BaseTestCase(TestCase):
    fixtures = ['initial_data.json',]

    def setUp(self):
        self.host = 'localhost:8000'
        self.client = Client(HTTP_HOST=self.host)
        self.user = User.objects.get(pk=1)

    def tearDown(self):
        pass

from resources import *
from serializers import *
from deserializers import *
