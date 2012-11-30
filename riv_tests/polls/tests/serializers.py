import datetime

from django.test import Client, TestCase
from django.core import serializers

from polls.tests import BaseTestCase
from polls.models import Poll, Choice

class BaseSerializerTestCase(BaseTestCase):

	def setUp(self):
		self.choice1 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Blue', votes=4)
		self.choice2 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Green', votes=4)

	def testSerializeAll(self):
		self.assertEqual(
			serializers.serialize('rest', Poll.objects.all()),
			[{'pub_date': datetime.datetime(2011, 10, 20, 18, 0), 'question': u'What is it about?', 'id': 1}, {'pub_date': datetime.datetime(2011, 10, 20, 18, 5), 'question': u'Is it about that?', 'id': 2}]
		)

	def testSerializeSingle(self):
		self.assertEqual(
			serializers.serialize('rest', Poll.objects.get(pk=1)),
			{'pub_date': datetime.datetime(2011, 10, 20, 18, 0), 'question': u'What is it about?', 'id': 1}
		)

	def testSerializeChoice(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1),
			{'votes': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceExtra(self):
		self.choice1.observer = 'Mr. James'
		self.assertEqual(
			serializers.serialize('rest', self.choice1, extra=['observer']),
			{'votes': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice, 'observer': 'Mr. James'}
		)
		self.assertEqual(
			serializers.serialize('rest', [self.choice1, self.choice2], extra=['observer']),
			[{'votes': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice, 'observer': 'Mr. James'}, {'votes': self.choice2.votes, 'poll': self.choice2.poll.id, 'id': self.choice2.id, 'choice': self.choice2.choice}]
		)

	def testSerializeChoiceFields(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, fields=['votes', 'choice']),
			{'votes': self.choice1.votes, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceExclude(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, exclude=['votes', 'choice']),
			{'poll': self.choice1.poll.id, 'id': self.choice1.id}
		)

	def testSerializeChoiceCombineFieldAndExclude(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, fields=['votes', 'choice', 'id'], exclude=['choice']),
			{'votes': self.choice1.votes, 'id': self.choice1.id}
		)

	def testSerializeChoiceInline(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, inline=True),
			{'votes': self.choice1.votes, 'poll': {'pub_date': self.choice1.poll.pub_date, 'question': self.choice1.poll.question, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceExcludeForeignKey(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, inline=True, exclude=['poll__question',]),
			{'votes': self.choice1.votes, 'poll': {'pub_date': self.choice1.poll.pub_date, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceExcludeForeignKeyWithoutInline(self):
		# TODO TODO TODO
		self.assertTrue(False)

	def testSerializeChoiceMap(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, map_fields={'votes': 'ballots'}),
			{'ballots': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceMapForeignKey(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, inline=True, map_fields={'poll__pub_date': 'poll__release_date'}),
			{'votes': self.choice1.votes, 'poll': {'release_date': self.choice1.poll.pub_date, 'question': self.choice1.poll.question, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

	def testSerializeChoiceMapForeignKeyWithoutInline(self):
		# TODO TODO TODO
		self.assertTrue(False)
		#self.assertEqual(
		#	serializers.serialize('rest', self.choice1, inline=True, map_fields={'poll__pub_date': 'poll__release_date'}),
		#	{'votes': self.choice1.votes, 'poll': {'release_date': self.choice1.poll.pub_date, 'question': self.choice1.poll.question, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
		#)

	def testSerializeChoiceMapDownForeignKey(self):
		self.assertEqual(
			serializers.serialize('rest', self.choice1, inline=True, map_fields={'poll__pub_date': 'polldate'}),
			{'votes': self.choice1.votes, 'polldate': self.choice1.poll.pub_date, 'poll': {'question': self.choice1.poll.question, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
		)

