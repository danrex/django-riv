import datetime
from django.test import Client, TestCase
from riv.utils import traverse_dict
from polls.tests import BaseTestCase

class BaseTraverseTestCase(BaseTestCase):

    def setUp(self):
        self.d = {'a': {'b': {'c': 'value'}}}
        self.d_list = {'a': {'b': [{'c': 'value1'}, {'c': 'value2'}]}}

    def testTraverseSimple(self):
        self.assertEqual(
            traverse_dict(self.d, ['a', 'b', 'c']),
            'value'
        )

    def testTraverseSimple2(self):
        self.assertEqual(
            traverse_dict(self.d, ['a', 'b']),
            {'c': 'value'}
        )

    def testTraverseSimpleReturnParent(self):
        self.assertEqual(
            traverse_dict(self.d, ['a', 'b', 'c'], return_parent=True),
            {'c': 'value'}
        )

    def testTraverseList(self):
        self.assertEqual(
            traverse_dict(self.d_list, ['a', 'b', 'c']),
            ['value1', 'value2']
        )

    def testTraverseList2(self):
        self.assertEqual(
            traverse_dict(self.d_list, ['a', 'b']),
            [{'c': 'value1'}, {'c': 'value2'}]
        )

    def testTraverseListReturnParent(self):
        self.assertEqual(
            traverse_dict(self.d_list, ['a', 'b', 'c'], return_parent=True),
            [{'c': 'value1'}, {'c': 'value2'}]
        )

