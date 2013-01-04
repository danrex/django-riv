from django.test import Client, TestCase
from polls.models import Poll, Choice

from polls.tests import BaseTestCase

class StandaloneReadOnlyTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/srpr/')
		self.assertEqual(response.status_code, 200)
		# Resultset is ordered by id.
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}, {"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/srwpr/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.post('/rest/srpr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testDeletePoll(self):
		response = self.client.delete('/rest/srpr/1')
		self.assertEqual(response.status_code, 405)

class StandalonePutOnlyTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/spuopr/')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/spuopr/1')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": []}'
		response = self.client.put('/rest/spuopr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [1]}'
		response = self.client.put('/rest/spuopr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(response.content, '')

	def testDeletePoll(self):
		response = self.client.delete('/rest/spuopr/1')
		self.assertEqual(response.status_code, 405)

class StandalonePostOnlyTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/spoopr/')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/spoopr/1')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [2]}'
		response = self.client.post('/rest/spoopr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 3, "tags": ["/rest/str/2"]}]')

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": []}'
		response = self.client.put('/rest/spoopr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testDeletePoll(self):
		response = self.client.delete('/rest/spoopr/1')
		self.assertEqual(response.status_code, 405)

class StandaloneDeleteOnlyTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/sdopr/')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/sdopr/1')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testPostPoll(self):
		put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
		response = self.client.put('/rest/sdopr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testPutPoll(self):
		put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
		response = self.client.put('/rest/sdopr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)
		self.assertEqual(response.content, '')

	def testDeletePoll(self):
		count = Poll.objects.all().count()
		response = self.client.delete('/rest/sdopr/1')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(count, Poll.objects.all().count()+1)

class StandaloneReadWriteTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/srwpr/')
		self.assertEqual(response.status_code, 200)
		# Resultset is ordered by id.
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}, {"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/srwpr/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}')

	def testPutPollWithoutId(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [3]}'
		response = self.client.put('/rest/srwpr/1', put_data, content_type='application/json')
		# object is not included in the response.
		self.assertEqual(response.status_code, 204)
		response = self.client.get('/rest/srwpr/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/3"]}, {"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}]')

	def testPutErrorPoll(self):
		put_data = '{"pub_date": "2011-10-20T19:00:00", "question": ""}'
		response = self.client.put('/rest/srwpr/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 400)

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

class StandaloneReadWriteTestCase2(BaseTestCase):

	def testPutPollWithoutId(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?"}'
		response = self.client.put('/rest/srwpr2/', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 405)

	def testPutPoll(self):
		"""
		PUT is UPDATE/REPLACE
		"""
		put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [1,2]}'
		response = self.client.put('/rest/srwpr2/1', put_data, content_type='application/json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2"]}')

		response = self.client.get('/rest/srwpr2/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2"]}, {"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}]')

class StandaloneExcludeGetTestCase(BaseTestCase):

	def testGetPolls(self):
		response = self.client.get('/rest/sego/')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '[{"question": "What is it about?", "id": 1}, {"question": "Is it about that?", "id": 2}]')

	def testGetSinglePoll(self):
		response = self.client.get('/rest/sego/1')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.content, '{"question": "What is it about?", "id": 1}')

