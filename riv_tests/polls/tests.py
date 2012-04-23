from django.test import Client, TestCase
from polls.models import Poll, Choice

class PollsTestCase(TestCase):
	fixtures = ['initial_data.json',]

	def setUp(self):
		self.client = Client(HTTP_HOST='localhost:8000')

	def tearDown(self):
		pass

class ReadOnlyTestCase(PollsTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/ropr/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}, {"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/ropr/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}]')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/ropr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/ropr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testDeletePoll(self):
		response = self.client.delete('/rest/ropr/1')
		self.assertEqual(response.status_code, 405)

class ReadWriteTestCase(PollsTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/rwpr/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}, {"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}]')

	def testPutPoll(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/rwpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 201)
		response = self.client.get('/rest/rwpr/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(set(response.content), set('[{"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}, {"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "id": 1}]'))

	def testPutErrorPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": ""}'
		response = self.client.put('/rest/rwpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 403)

	def testDeletePoll(self):
		count = Poll.objects.all().count()
		response = self.client.delete('/rest/rwpr/1')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(count, Poll.objects.all().count()+1)

class StandaloneReadOnlyTestCase(PollsTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/srpr/')
		self.assertEqual(response.status_code, 200)
		# Resultset is ordered by id.
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}, {"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/srpr/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}]')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srpr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testDeletePoll(self):
		response = self.client.delete('/rest/srpr/1')
		self.assertEqual(response.status_code, 405)

class StandaloneReadWriteTestCase(PollsTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/srwpr/')
		self.assertEqual(response.status_code, 200)
		# Resultset is ordered by id.
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}, {"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/srwpr/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 18:00:00", "question": "What is it about?", "id": 1}]')

	def testPutPollWithoutId(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr/1', put_data, content_type='application/json')
		# object is not included in the response.
		self.assertEqual(response.status_code, 204)
		response = self.client.get('/rest/srwpr/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(set(response.content), set('[{"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}, {"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "id": 1}]'))

	def testPutErrorPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": ""}'
		response = self.client.put('/rest/srwpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 403)

	def testDeleteSinglePoll(self):
		count = Poll.objects.all().count()
		response = self.client.delete('/rest/srwpr/1')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(count, Poll.objects.all().count()+1)

	def testDeleteListPoll(self):
		count = Poll.objects.all().count()
		response = self.client.delete('/rest/srwpr/1;2')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(count, Poll.objects.all().count()+2)

	def testDeleteAllPoll(self):
		count = Poll.objects.all().count()
		response = self.client.delete('/rest/srwpr/')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(count, Poll.objects.all().count()+2)

class StandaloneReadWriteTestCase2(PollsTestCase):

	def testPutPollWithoutId(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr2/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr2/1', put_data, content_type='application/json')
		# object IS included in the response.
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "id": 1}]')

		response = self.client.get('/rest/srwpr2/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(set(response.content), set('[{"pub_date": "2011-10-20 18:05:00", "question": "Is it about that?", "id": 2}, {"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "id": 1}]'))

