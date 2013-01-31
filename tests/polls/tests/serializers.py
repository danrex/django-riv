import datetime

from django.test import Client, TestCase
from django.core import serializers

from polls.tests import BaseTestCase
from polls.models import Poll, Choice

import xml.etree.ElementTree as ET

# This method is a simplified version of xml_compare found on
# https://bitbucket.org/ianb/formencode
# It has been modified to ignore the order of tags.
def xml_compare(x1, x2):
    if x1.tag != x2.tag:
        return False
    for name, value in x1.attrib.items():
        if x2.attrib.get(name) != value:
            return False
    for name in x2.attrib.keys():
        if name not in x1.attrib:
            return False
    if not text_compare(x1.text, x2.text):
        return False
    if not text_compare(x1.tail, x2.tail):
        return False
    cl1 = sorted(x1.getchildren(), key=lambda e: e.tag)
    cl2 = sorted(x2.getchildren(), key=lambda e: e.tag)
    if len(cl1) != len(cl2):
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not xml_compare(c1, c2):
            return False
    return True


def text_compare(t1, t2):
    if not t1 and not t2:
        return True
    if t1 == '*' or t2 == '*':
        return True
    return (t1 or '').strip() == (t2 or '').strip()

class BaseSerializerTestCase(BaseTestCase):

    def setUp(self):
        self.poll1 = Poll.objects.get(pk=1)
        self.poll2 = Poll.objects.get(pk=2)
        self.choice1 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Blue', votes=4)
        self.choice2 = Choice.objects.create(poll=Poll.objects.get(pk=1), choice='Green', votes=4)

    def testSerializeAll(self):
        self.assertEqual(
            serializers.serialize('rest', Poll.objects.all()),
            [{'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [x.id for x in self.poll1.tags.all()]}, {'pub_date': self.poll2.pub_date, 'question': self.poll2.question, 'id': self.poll2.id, 'tags': [x.id for x in self.poll2.tags.all()]}]
        )

    def testSerializeSingle(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [x.id for x in self.poll1.tags.all()]}
        )

    def testSerializePollReverseChoice(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, reverse_fields=['choice_set']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'choice_set': [1, 2, 3, 5, 6], 'tags': [1, 2, 3]}
        )

    def testSerializePollReverseChoiceInline(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, reverse_fields=['choice_set'], inline=['choice_set']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'choice_set': [{'choice': x.choice, 'id': x.id, 'poll': x.poll.id, 'votes': x.votes} for x in self.poll1.choice_set.all()], 'tags': [1, 2, 3]}
        )

    def testSerializePollReverseChoiceInlineMap(self):
        self.maxDiff = None # show the full diff output for long strings
        self.assertEqual(
                serializers.serialize('rest', self.poll1, reverse_fields=['choice_set'], inline=['choice_set'], map_fields={'choice_set__choice': 'choice_set__text'}),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'choice_set': [{'text': x.choice, 'id': x.id, 'poll': x.poll.id, 'votes': x.votes} for x in self.poll1.choice_set.all()], 'tags': [1, 2, 3]}
        )

    def testSerializePollReverseChoiceInlineMapDown(self):
        self.maxDiff = None # show the full diff output for long strings
        self.assertEqual(
                serializers.serialize('rest', self.poll1, reverse_fields=['choice_set'], inline=['choice_set'], map_fields={'choice_set__choice': 'choicetext'}),
                {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'choicetext': [x.choice for x in self.poll1.choice_set.all()], 'choice_set': [{'id': x.id, 'poll': x.poll.id, 'votes': x.votes} for x in self.poll1.choice_set.all()], 'tags': [1, 2, 3]}
        )

    def testSerializePollManyToManyInline(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, inline=['tags']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [{'name': x.name, 'id': x.id} for x in self.poll1.tags.all()]}
        )

    def testSerializePollExcludeManyToManyAttribute(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, exclude=['tags__name'], inline=['tags']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [{'id': x.id} for x in self.poll1.tags.all()]}
        )

    def testSerializeMultiplePollsExcludeManyToManyAttribute(self):
        self.assertEqual(
            serializers.serialize('rest', [self.poll1, self.poll2], exclude=['tags__name'], inline=['tags']),
            [{'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [{'id': x.id} for x in self.poll1.tags.all()]}, {'pub_date': self.poll2.pub_date, 'question': self.poll2.question, 'id': self.poll2.id, 'tags': [{'id': x.id} for x in self.poll2.tags.all()]}]
        )

    def testSerializePollRenameManyToManyAttribute(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, map_fields={'tags__name': 'tags__text'}, inline=['tags']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [{'text': x.name, 'id': x.id} for x in self.poll1.tags.all()]}
        )

    def testSerializeMultiplePollsRenameManyToManyAttribute(self):
        self.assertEqual(
            serializers.serialize('rest', [self.poll1, self.poll2], map_fields={'tags__name': 'tags__text'}, inline=['tags']),
            [{'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [{'text': x.name, 'id': x.id} for x in self.poll1.tags.all()]}, {'pub_date': self.poll2.pub_date, 'question': self.poll2.question, 'id': self.poll2.id, 'tags': [{'text': x.name, 'id': x.id} for x in self.poll2.tags.all()]}]
        )

    def testSerializePollMapDownManyToManyAttribute(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, map_fields={'tags__name': 'tagname'}, inline=['tags']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tagname': [x.name for x in self.poll1.tags.all()], 'tags': [{'id': x.id} for x in self.poll1.tags.all()]}
        )

    def testSerializePollMapDownManyToManyAttributeAndRemoveRemains(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, map_fields={'tags__name': 'tagname'}, inline=['tags'], exclude=['tags']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tagname': [x.name for x in self.poll1.tags.all()]}
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

    def testSerializeChoiceExtraCallable(self):
        self.assertEqual(
            serializers.serialize('rest', self.poll1, extra=['was_published_today']),
            {'pub_date': self.poll1.pub_date, 'question': self.poll1.question, 'id': self.poll1.id, 'tags': [x.id for x in self.poll1.tags.all()], 'was_published_today': self.poll1.was_published_today()}
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
            serializers.serialize('rest', self.choice1, inline=['poll',]),
            {'votes': self.choice1.votes, 'poll': {'pub_date': self.choice1.poll.pub_date, 'question': self.choice1.poll.question, 'id': self.choice1.poll.id, 'tags': [x.id for x in self.choice1.poll.tags.all()]}, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

    def testSerializeChoiceExcludeForeignKey(self):
        self.assertEqual(
            serializers.serialize('rest', self.choice1, inline=['poll',], exclude=['poll__question', 'poll__tags']),
            {'votes': self.choice1.votes, 'poll': {'pub_date': self.choice1.poll.pub_date, 'id': self.choice1.poll.id}, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

    def testSerializeChoiceExcludeForeignKeyWithoutInline(self):
        """
        This test should simply ignore the exclude setting.
        """
        self.assertEqual(
            serializers.serialize('rest', self.choice1, exclude=['poll__question',]),
            {'votes': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

    def testSerializeChoiceMap(self):
        self.assertEqual(
            serializers.serialize('rest', self.choice1, map_fields={'votes': 'ballots'}),
            {'ballots': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

    def testSerializeMultipleChoiceMap(self):
        self.assertEqual(
            serializers.serialize('rest', [self.choice1, self.choice2], map_fields={'votes': 'ballots'}),
            [{'ballots': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice}, {'ballots': self.choice2.votes, 'poll': self.choice2.poll.id, 'id': self.choice2.id, 'choice': self.choice2.choice}]
        )

    def testSerializeChoiceMapForeignKey(self):
        self.assertEqual(
            serializers.serialize('rest', self.choice1, inline=['poll',], map_fields={'poll__pub_date': 'poll__release_date'}),
            {'votes': self.choice1.votes, 'poll': {'release_date': self.choice1.poll.pub_date, 'question': self.choice1.poll.question, 'id': self.choice1.poll.id, 'tags': [x.id for x in self.choice1.poll.tags.all()]}, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

    def testSerializeChoiceMapForeignKeyWithoutInline(self):
        self.assertRaisesMessage(serializers.base.SerializationError, "Invalid key 'poll__pub_date' in map_fields. Did you add 'poll' to the inline fields?", serializers.serialize, 'rest', self.choice1, map_fields={'poll__pub_date': 'poll__release_date'})

    def testSerializeChoiceMapForeignKeyCrossMapping(self):
        self.assertRaisesMessage(serializers.base.SerializationError, "Crossmapping between different ForeignKey fields is currently not supported.", serializers.serialize, 'rest', self.choice1, inline=['poll'], map_fields={'poll__pub_date': 'lala__release_date'})

    def testSerializeChoiceMapDownForeignKey(self):
        self.assertEqual(
            serializers.serialize('rest', self.choice1, inline=['poll',], map_fields={'poll__pub_date': 'polldate'}),
            {'votes': self.choice1.votes, 'polldate': self.choice1.poll.pub_date, 'poll': {'question': self.choice1.poll.question, 'id': self.choice1.poll.id, 'tags': [x.id for x in self.choice1.poll.tags.all()]}, 'id': self.choice1.id, 'choice': self.choice1.choice}
        )

class XmlSerializerTestCase(BaseSerializerTestCase):

    def testSerializeAll(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><poll><pub_date>%s</pub_date><question>%s</question><id>%d</id><tags>%s</tags></poll><poll><pub_date>%s</pub_date><question>%s</question><id>%d</id><tags>%s</tags></poll></objects>' % (self.poll1.pub_date, self.poll1.question, self.poll1.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.poll1.tags.all()]) + "</tag>").replace("<tag></tag>", ""), self.poll2.pub_date, self.poll2.question, self.poll2.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.poll2.tags.all()]) + "</tag>").replace("<tag></tag>", ""))
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', Poll.objects.all()))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeSingle(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><poll><pub_date>%s</pub_date><question>%s</question><id>%d</id><tags>%s</tags></poll></objects>' % (self.poll1.pub_date, self.poll1.question, self.poll1.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.poll1.tags.all()]) + "</tag>").replace("<tag></tag>", ""))
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', Poll.objects.get(pk=1)))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoice(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><poll>%d</poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.id, self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceExtra(self):
        self.choice1.observer = 'Mr. James'
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><observer>%s</observer><votes>%d</votes><poll>%d</poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.observer, self.choice1.votes, self.choice1.poll.id, self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, extra=['observer']))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

        self.assertEqual(
            serializers.serialize('rest', [self.choice1, self.choice2], extra=['observer']),
            [{'votes': self.choice1.votes, 'poll': self.choice1.poll.id, 'id': self.choice1.id, 'choice': self.choice1.choice, 'observer': 'Mr. James'}, {'votes': self.choice2.votes, 'poll': self.choice2.poll.id, 'id': self.choice2.id, 'choice': self.choice2.choice}]
        )

    def testSerializeChoiceExtraTwoObjects(self):
        self.choice1.observer = 'Mr. James'
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><observer>%s</observer><votes>%d</votes><poll>%d</poll><id>%d</id><choice>%s</choice></choice><choice><votes>%d</votes><poll>%d</poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.observer, self.choice1.votes, self.choice1.poll.id, self.choice1.id, self.choice1.choice, self.choice2.votes, self.choice2.poll.id, self.choice2.id, self.choice2.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', [self.choice1, self.choice2], extra=['observer']))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceFields(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, fields=['votes', 'choice']))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceExclude(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><poll>%d</poll><id>%d</id></choice></objects>' % (self.choice1.poll.id, self.choice1.id)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, exclude=['votes', 'choice']))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceCombineFieldAndExclude(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><id>%d</id></choice></objects>' % (self.choice1.votes, self.choice1.id)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, fields=['votes', 'choice', 'id'], exclude=['choice']))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceInline(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><poll><pub_date>%s</pub_date><question>%s</question><id>%d</id><tags>%s</tags></poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.pub_date, self.choice1.poll.question, self.choice1.poll.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.choice1.poll.tags.all()]) + "</tag>").replace("<tag></tag>", ""), self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, inline=['poll',]))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceExcludeForeignKey(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><poll><pub_date>%s</pub_date><id>%d</id><tags><tag>%d</tag><tag>%d</tag><tag>%d</tag></tags></poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.pub_date, self.choice1.poll.id, self.choice1.poll.tags.all()[0].id, self.choice1.poll.tags.all()[1].id, self.choice1.poll.tags.all()[2].id, self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, inline=['poll',], exclude=['poll__question',]))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceExcludeForeignKeyWithoutInline(self):
        """
        This test should simply ignore the exclude setting.
        """
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><poll>%d</poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.id, self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, exclude=['poll__question',]))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceMap(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><ballots>%d</ballots><poll>%d</poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.id, self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, map_fields={'votes': 'ballots'}))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceMapForeignKey(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%d</votes><poll><release_date>%s</release_date><question>%s</question><id>%d</id><tags>%s</tags></poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.pub_date, self.choice1.poll.question, self.choice1.poll.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.choice1.poll.tags.all()]) + "</tag>").replace("<tag></tag>", ""), self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, inline=['poll',], map_fields={'poll__pub_date': 'poll__release_date'}))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

    def testSerializeChoiceMapForeignKeyWithoutInline(self):
        self.assertRaisesMessage(serializers.base.SerializationError, "Invalid key 'poll__pub_date' in map_fields. Did you add 'poll' to the inline fields?", serializers.serialize, 'rest', self.choice1, map_fields={'poll__pub_date': 'poll__release_date'})

    def testSerializeChoiceMapDownForeignKey(self):
        xmlstring = '<?xml version="1.0" encoding="utf-8"?><objects><choice><votes>%s</votes><polldate>%s</polldate><poll><question>%s</question><id>%d</id><tags>%s</tags></poll><id>%d</id><choice>%s</choice></choice></objects>' % (self.choice1.votes, self.choice1.poll.pub_date, self.choice1.poll.question, self.choice1.poll.id, ("<tag>" + "</tag><tag>".join([str(x.id) for x in self.choice1.poll.tags.all()]) + "</tag>").replace("<tag></tag>", ""), self.choice1.id, self.choice1.choice)
        result_xml = ET.fromstring(xmlstring)
        serialized_xml = ET.fromstring(serializers.serialize('restxml', self.choice1, inline=['poll',], map_fields={'poll__pub_date': 'polldate'}))
        self.assertTrue(xml_compare(result_xml, serialized_xml))

