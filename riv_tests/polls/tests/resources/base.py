from django.test import Client, TestCase
from polls.models import Poll, Choice

from polls.tests import BaseTestCase

class ReadOnlyTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/ropr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}, {"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}]')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/ropr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}')

    def testPostPoll(self):
        put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.put('/rest/ropr/', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def testPutPoll(self):
        put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?"}'
        response = self.client.put('/rest/ropr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def testDeletePoll(self):
        response = self.client.delete('/rest/ropr/1')
        self.assertEqual(response.status_code, 405)

class PutOnlyTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/puopr/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/puopr/1')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testPostPoll(self):
        put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.post('/rest/puopr/', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)

    def testPutPoll(self):
        put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.put('/rest/puopr/1', put_data, content_type='application/json')
        # Update an existing object and return the content == 200
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1"]}')
        response = self.client.get('/rest/ropr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1"]}')

    def testDeletePoll(self):
        response = self.client.delete('/rest/puopr/1')
        self.assertEqual(response.status_code, 405)

class PostOnlyTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/poopr/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/poopr/1')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testPostPoll(self):
        put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.post('/rest/poopr/', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 3, "tags": ["/rest/str/1"]}')

    def testPutPoll(self):
        put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.put('/rest/poopr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testDeletePoll(self):
        response = self.client.delete('/rest/poopr/1')
        self.assertEqual(response.status_code, 405)

class DeleteOnlyTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/dopr/')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/dopr/1')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testPostPoll(self):
        put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.put('/rest/dopr/', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testPutPoll(self):
        put_data = '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.put('/rest/dopr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.content, '')

    def testDeletePoll(self):
        count = Poll.objects.all().count()
        response = self.client.delete('/rest/dopr/1')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(count, Poll.objects.all().count()+1)

class ReadWriteTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/rwpr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}, {"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}]')

    def testPutPoll(self):
        """
        PUT is UPDATE/REPLACE
        """
        count = Poll.objects.all().count()
        put_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.put('/rest/rwpr/1', put_data, content_type='application/json')
        # Update an existing object and return the content == 200
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1"]}')
        response = self.client.get('/rest/rwpr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"pub_date": "2011-10-20T19:00:00", "question": "is that allowed?", "id": 1, "tags": ["/rest/str/1"]}, {"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}]')
        # Number of objects remains unchanged
        self.assertEqual(count, Poll.objects.all().count())

    def testPutRenderPoll(self):
        """
        PUT is UPDATE/REPLACE
        """
        count = Poll.objects.all().count()
        put_data = '{"pub_date": "2011-10-20 19:01:00", "question": "is the object rendered?", "tags": [1, 2]}'
        response = self.client.put('/rest/rwrpr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:01:00", "question": "is the object rendered?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2"]}')
        response = self.client.get('/rest/rwrpr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.content), set('[{"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}, {"pub_date": "2011-10-20T19:01:00", "question": "is the object rendered?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2"]}]'))
        self.assertEqual(count, Poll.objects.all().count())

    def testPostPoll(self):
        count = Poll.objects.all().count()
        post_data = '{"pub_date": "2011-10-20 19:05:00", "question": "is this a new object?", "tags": [2]}'
        response = self.client.post('/rest/rwpr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue('Location' in response)
        self.assertEqual(response["Location"], 'http://' + self.host + "/rest/ropr/3")
        self.assertEqual(response.content, '')
        self.assertEqual(count, Poll.objects.all().count()-1)

    def testPostRenderPoll(self):
        count = Poll.objects.all().count()
        post_data = '{"pub_date": "2011-10-20 19:05:00", "question": "is this a new object?", "tags": [2]}'
        response = self.client.post('/rest/rwrpr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue('Location' in response)
        self.assertEqual(response["Location"], 'http://' + self.host + "/rest/ropr/3")
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T19:05:00", "question": "is this a new object?", "id": 3, "tags": ["/rest/str/2"]}')
        self.assertEqual(count, Poll.objects.all().count()-1)

    def testPutErrorPoll(self):
        count = Poll.objects.all().count()
        put_data = '{"pub_date": "2011-10-20 19:00:00", "question": ""}'
        response = self.client.put('/rest/rwpr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(count, Poll.objects.all().count())

    def testDeletePoll(self):
        count = Poll.objects.all().count()
        response = self.client.delete('/rest/rwpr/1')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(count, Poll.objects.all().count()+1)

class BatchPostTestCase(BaseTestCase):

    def testPostPoll(self):
        count = Poll.objects.all().count()
        post_data = '{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [2]}'
        response = self.client.post('/rest/bppr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue('Location' in response)
        self.assertEqual(response["Location"], 'http://' + self.host + "/rest/ropr/3")
        self.assertEqual(response.content, "")
        self.assertEqual(count, Poll.objects.all().count()-1)

    def testBatchPostPoll(self):
        count = Poll.objects.all().count()
        post_data = '[{"pub_date": "2011-10-20 19:00:00", "question": "is that allowed?", "tags": [2]}, {"pub_date": "2011-10-20 19:30:00", "question": "how is the weather?", "tags": [1]}]'
        response = self.client.post('/rest/bppr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 204)
        # The location header points to the first object
        self.assertTrue('Location' in response)
        self.assertEqual(response["Location"], 'http://' + self.host + "/rest/ropr/3")
        self.assertEqual(response.content, "")
        self.assertEqual(count, Poll.objects.all().count()-2)

#class BatchDeleteTestCase(BaseTestCase):
#
#   def testBatchDeletePollFail(self):
#       count = Poll.objects.all().count()
#       response = self.client.delete('/rest/dopr/')
#       self.assertEqual(response.status_code, 404)
#
#   def testBatchDeletePollSuccess(self):
#       count = Poll.objects.all().count()
#       response = self.client.delete('/rest/bdpr/')
#       self.assertEqual(response.status_code, 204)
#       self.assertEqual(Poll.objects.all().count(), 0)

class RedirectTestCase(BaseTestCase):

    def testNotLoggedIn(self):
        response = self.client.get('/rest/result/1')
        self.assertEqual(response.status_code, 401)

    def testLoggedIn(self):
        self.user.set_password('whatever')
        self.user.save()
        self.client.login(username='johndoe', password='whatever')
        response = self.client.get('/rest/result/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"choice": [{"votes": 1, "name": "Red"}, {"votes": 2, "name": "Green"}, {"votes": 3, "name": "Blue"}]}]')

class UnsupportedFormatTestCase(BaseTestCase):

    def testJSONFallback(self):
        response = self.client.get('/rest/ropr/?format=guglhupf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}, {"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}]')

    def testNoFallback(self):
        response = self.client.get('/rest/nfpr/?format=guglhupf')
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.content, '')

class RelatedAsIdsTestCase(BaseTestCase):

    def relatedAsUrls(self):
        response = self.client.get('/rest/ropr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": ["/rest/str/1", "/rest/str/2", "/rest/str/3"]}')

    def relatedAsIds(self):
        response = self.client.get('/rest/raipr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "question": "What is it about?", "id": 1, "tags": [1, 2, 3]}')

class FieldsTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/fpr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"question": "Is it about that?"}, {"question": "What is it about?"}]')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/fpr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"question": "What is it about?"}')

    def testPostPoll(self):
        count = Poll.objects.all().count()
        post_data = '{"pub_date": "2011-10-20 21:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.post('/rest/fpr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, '[{"error": {"pub_date": ["This field is required."], "tags": ["This field is required."]}}]')
        self.assertEqual(count, Poll.objects.all().count())

    def testPutPoll(self):
        """
        PUT is UPDATE/REPLACE
        """
        count = Poll.objects.all().count()
        put_data = '{"pub_date": "2011-10-20 20:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.put('/rest/fpr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, '[{"error": {"pub_date": ["This field is required."], "tags": ["This field is required."]}}]')
        # Number of objects remains unchanged
        self.assertEqual(count, Poll.objects.all().count())

class ExcludeTestCase(BaseTestCase):

    def testGetPolls(self):
        response = self.client.get('/rest/excpr/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '[{"pub_date": "2011-10-20T18:05:00", "id": 2}, {"pub_date": "2011-10-20T18:00:00", "id": 1}]')

    def testGetSinglePoll(self):
        response = self.client.get('/rest/excpr/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:00:00", "id": 1}')

    def testPostPoll(self):
        count = Poll.objects.all().count()
        post_data = '{"pub_date": "2011-10-20 21:00:00", "question": "is that allowed?", "tags": [1]}'
        response = self.client.post('/rest/excpr/', post_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, '[{"error": {"question": ["This field is required."], "tags": ["This field is required."]}}]')
        # Number of objects remains unchanged
        self.assertEqual(count, Poll.objects.all().count())

    def testPutPoll(self):
        """
        PUT is UPDATE/REPLACE
        """
        count = Poll.objects.all().count()
        put_data = '{"pub_date": "2011-10-20 20:00:00", "question": "is that allowed?", "tags": []}'
        response = self.client.put('/rest/excpr/1', put_data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, '[{"error": {"question": ["This field is required."], "tags": ["This field is required."]}}]')
        self.assertEqual(count, Poll.objects.all().count())

class InlineTestCase(BaseTestCase):

    def testGetSinglePoll(self):
        response = self.client.get('/rest/ipr/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": [{"name": "Political", "id": 1}]}')

class ExtraTestCase(BaseTestCase):

    def testGetSinglePoll(self):
        response = self.client.get('/rest/extpr/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"pub_date": "2011-10-20T18:05:00", "was_published_today": false, "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}')

class MapTestCase(BaseTestCase):

    def testGetSinglePoll(self):
        response = self.client.get('/rest/mpr/2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '{"poll_date": "2011-10-20T18:05:00", "question": "Is it about that?", "id": 2, "tags": ["/rest/str/1"]}')
