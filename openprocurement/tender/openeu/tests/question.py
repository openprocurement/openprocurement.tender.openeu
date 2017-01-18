# -*- coding: utf-8 -*-
import unittest

from openprocurement.tender.openeu.tests.base import BaseTenderContentWebTest, test_tender_data, test_lots, test_bids
from openprocurement.api.tests.question import BaseTenderQuestionResourceTest, BaseTenderLotQuestionResourceTest

class BaseEUTenderQuestionResourceTest(object):

    initial_auth = ('Basic', ('broker', ''))

    def test_create_tender_question(self):
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        question = response.json['data']
        self.assertEqual(question['author']['name'], test_bids[0]['tenderers'][0]['name'])
        self.assertIn('id', question)
        self.assertIn(question['id'], response.headers['Location'])

        self.time_shift('enquiryPeriod_ends')

        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add question only in enquiryPeriod")

        self.time_shift('active.pre-qualification')
        self.check_chronograph()
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add question only in enquiryPeriod")

    def test_get_tender_question_eu(self):
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        question = response.json['data']

        response = self.app.get('/tenders/{}/questions/{}'.format(self.tender_id, question['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data']), set([u'id', u'date', u'title', u'description', u'questionOf']))

        response = self.app.patch_json('/tenders/{}/questions/{}?acc_token={}'.format(self.tender_id, question['id'], self.tender_token), {"data": {"answer": "answer"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["answer"], "answer")
        self.assertIn('dateAnswered', response.json['data'])
        question["answer"] = "answer"
        question['dateAnswered'] = response.json['data']['dateAnswered']

        self.time_shift('active.pre-qualification')
        self.check_chronograph()

        response = self.app.get('/tenders/{}/questions/{}'.format(self.tender_id, question['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'], question)

        response = self.app.get('/tenders/{}/questions/some_id'.format(self.tender_id), status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'question_id'}
        ])

        response = self.app.get('/tenders/some_id/questions/some_id', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

    def test_get_tender_questions_eu(self):
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        question = response.json['data']

        response = self.app.get('/tenders/{}/questions'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(set(response.json['data'][0]), set([u'id', u'date', u'title', u'description', u'questionOf']))

        response = self.app.patch_json('/tenders/{}/questions/{}?acc_token={}'.format(self.tender_id, question['id'], self.tender_token), {"data": {"answer": "answer"}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["answer"], "answer")
        self.assertIn('dateAnswered', response.json['data'])
        question["answer"] = "answer"
        question['dateAnswered'] = response.json['data']['dateAnswered']

        self.time_shift('active.pre-qualification')
        self.check_chronograph()

        response = self.app.get('/tenders/{}/questions'.format(self.tender_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data'][0], question)

        response = self.app.get('/tenders/some_id/questions', status=404)
        self.assertEqual(response.status, '404 Not Found')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Not Found', u'location':
                u'url', u'name': u'tender_id'}
        ])

class TenderQuestionResourceTest(BaseTenderContentWebTest, BaseTenderQuestionResourceTest, BaseEUTenderQuestionResourceTest):
    test_tender_data = test_tender_data
    status = "unsuccessful"

class TenderEULotQuestionResourceTest(BaseTenderContentWebTest, BaseTenderLotQuestionResourceTest):
    initial_auth = ('Basic', ('broker', ''))
    initial_lots = 2 * test_lots
    def test_create_tender_question(self):
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        question = response.json['data']
        self.assertEqual(question['author']['name'], test_bids[0]['tenderers'][0]['name'])
        self.assertIn('id', question)
        self.assertIn(question['id'], response.headers['Location'])

        self.time_shift('enquiryPeriod_ends')

        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add question only in enquiryPeriod")

        self.time_shift('active.pre-qualification')
        self.check_chronograph()
        response = self.app.post_json('/tenders/{}/questions'.format(
            self.tender_id), {'data': {'title': 'question title', 'description': 'question description', 'author': test_bids[0]['tenderers'][0]}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['errors'][0]["description"], "Can add question only in enquiryPeriod")

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderQuestionResourceTest))
    suite.addTest(unittest.makeSuite(TenderEULotQuestionResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
