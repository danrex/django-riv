import datetime

from django.test import Client, TestCase
from django.core import serializers

from polls.tests import BaseTestCase
from polls.models import Poll, Choice

class BaseDeserializerTestCase(BaseTestCase):

    def setUp(self):
        self.choice1 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Blue', votes=4)
        self.choice2 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Green', votes=4)

    def testDeserializeAll(self):
        q1 = u'Is it new?'
        q2 = u'And is that new?'
        for obj in serializers.deserialize(
            'rest',
            [{'pub_date': datetime.datetime(2011, 10, 20, 18, 0), 'question': q1, 'id': 1}, {'pub_date': datetime.datetime(2011, 10, 20, 18, 5), 'question': q2, 'id': 2}],
            model='polls.Poll'):
            obj.save()

        self.assertEqual(Poll.objects.get(pk=1).question, q1)
        self.assertEqual(Poll.objects.get(pk=2).question, q2)

    def testDeserializeSingle(self):
        q1 = u'Is it new?'
        for obj in serializers.deserialize(
            'rest',
            {'pub_date': datetime.datetime(2011, 10, 20, 18, 0), 'question': q1, 'id': 1},
            model='polls.Poll'):
            obj.save()

        self.assertEqual(Poll.objects.get(pk=1).question, q1)


    def testDeserializeChoice(self):
        for obj in serializers.deserialize(
            'rest',
            {'votes': 5, 'poll': 1, 'id': 1, 'choice': 'Red'},
            model='polls.Choice'):
            obj.save()
        self.assertEqual(Choice.objects.get(pk=1).votes, 5)
        self.assertEqual(Choice.objects.get(pk=1).choice, 'Red')
        self.assertEqual(Choice.objects.get(pk=1).poll.id, 1)

    def testDeserializeChoiceWithMappedFields(self):
        for obj in serializers.deserialize(
            'rest',
            {'ballots': 99, 'poll': 1, 'id': 1, 'selection': 'Miller'},
            model='polls.Choice',
            map_fields={'votes': 'ballots', 'choice': 'selection'}):
            obj.save()
        self.assertEqual(Choice.objects.get(pk=1).votes, 99)
        self.assertEqual(Choice.objects.get(pk=1).choice, 'Miller')
        self.assertEqual(Choice.objects.get(pk=1).poll.id, 1)
