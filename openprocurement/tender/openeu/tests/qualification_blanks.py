# -*- coding: utf-8 -*-
# TenderQualificationResourceTest


def post_tender_qualifications(self):
    response = self.app.post_json('/tenders/{}/qualifications'.format(self.tender_id), {"data": {}}, status=405)
    self.assertEqual(response.status, '405 Method Not Allowed')

    data = {"bidID": "some_id", "status": "pending"}
    response = self.app.post_json('/tenders/{}/qualifications'.format(self.tender_id), {"data": data}, status=405)
    self.assertEqual(response.status, '405 Method Not Allowed')

    data = {"bidID": "1234" * 8, "status": "pending", "id": "12345678123456781234567812345678"}
    response = self.app.post_json('/tenders/{}/qualifications'.format(self.tender_id), {"data": data}, status=405)
    self.assertEqual(response.status, '405 Method Not Allowed')

    data = {"bidID": "1234" * 8, "status": "pending", "id": "12345678123456781234567812345678"}
    response = self.app.post_json('/tenders/{}/qualifications/{}'.format(self.tender_id, data['id']), {"data": data},
                                  status=404)
    self.assertEqual(response.status, '404 Not Found')

    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    qualifications = response.json['data']
    data = {"bidID": "1234" * 8, "status": "pending", 'id': qualifications[0]['id']}
    response = self.app.post_json('/tenders/{}/qualifications/{}'.format(self.tender_id, qualifications[0]['id']),
                                  {"data": data}, status=405)
    self.assertEqual(response.status, '405 Method Not Allowed')


def get_tender_qualifications_collection(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 2)

    response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualification_bid_ids = [q['bidID'] for q in qualifications]
    for bid in response.json['data']:
        self.assertIn(bid['id'], qualification_bid_ids)
        qualification_bid_ids.remove(bid['id'])


def patch_tender_qualifications(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 2)

    q1_id = qualifications[0]['id']
    q2_id = qualifications[1]['id']

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q1_id, self.tender_token),
        {"data": {"title": "title", "description": "description",
                  "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['title'], 'title')
    self.assertEqual(response.json['data']['description'], 'description')
    self.assertEqual(response.json['data']['qualified'], True)
    self.assertEqual(response.json['data']['eligible'], True)
    self.assertEqual(response.json['data']['date'], qualifications[0]['date'])

    # first qualification manipulations
    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q1_id, self.tender_token),
        {"data": {"title": "title", "description": "description",
                  "status": "active", "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')
    self.assertNotEqual(response.json['data']['date'], qualifications[0]['date'])
    self.assertEqual(response.json['data']['title'], 'title')
    self.assertEqual(response.json['data']['description'], 'description')

    for status in ['pending', 'unsuccessful']:
        response = self.app.patch_json(
            '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q1_id, self.tender_token),
            {"data": {'status': status}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], "Can't update qualification status")

    ## activequalification can be cancelled
    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q1_id, self.tender_token),
        {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')

    ## cancelled status is terminated
    for status in ['pending', 'active', 'unsuccessful']:
        response = self.app.patch_json(
            '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q1_id, self.tender_token),
            {"data": {'status': status}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'],
                         "Can't update qualification in current cancelled qualification status")

    # second qualification manipulations
    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q2_id, self.tender_token),
        {"data": {'status': 'unsuccessful'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    for status in ['pending', 'active']:
        response = self.app.patch_json(
            '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q2_id, self.tender_token),
            {"data": {'status': status, "qualified": True, "eligible": True}}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.json['errors'][0]['description'], "Can't update qualification status")

    ## unsuccessful qualification can be cancelled
    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q2_id, self.tender_token),
        {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')

    # list for new qualification
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 4)
    q1 = qualifications[0]
    q3 = qualifications[2]
    self.assertEqual(q1['bidID'], q3['bidID'])
    q2 = qualifications[1]
    q4 = qualifications[3]
    self.assertEqual(q2['bidID'], q4['bidID'])

    self.assertEqual(q3['status'], 'pending')

    # cancel pending qualification
    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q3['id'], self.tender_token),
        {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')

    # one more qualification should be generated
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 5)
    self.assertEqual(q3['bidID'], qualifications[4]['bidID'])

    # activate rest qualifications
    for q_id in (qualifications[3]['id'], qualifications[4]['id']):
        response = self.app.patch_json(
            '/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, q_id, self.tender_token),
            {"data": {"status": "active", "qualified": True, "eligible": True}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], 'active')


def get_tender_qualifications(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    qualifications = response.json['data']
    for qualification in qualifications:
        response = self.app.get('/tenders/{}/qualifications/{}?acc_token={}'.format(
            self.tender_id, qualification['id'], self.tender_token))
        self.assertEqual(response.status, '200 OK')


def patch_tender_qualifications_after_status_change(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.status, '200 OK')
    qualifications = response.json['data']
    for qualification in qualifications:
        response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
            self.tender_id, qualification['id'], self.tender_token),
            {'data': {"status": "active", "qualified": True, "eligible": True}})
        self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, qualification['id'], self.tender_token), {'data': {"status": "cancelled"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"description": u"Can't update qualification in current (active.pre-qualification.stand-still) tender status",
         u'location': u'body', u'name': u'data'}])

# Tender2LotQualificationResourceTest


def lot_patch_tender_qualifications(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualifications[2]['id'], self.tender_token),
                                  {"data": {"status": "active", "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualifications[1]['id'], self.tender_token),
                                  {"data": {'status': 'unsuccessful'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'unsuccessful')

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualifications[0]['id'], self.tender_token),
                                  {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')


def lot_get_tender_qualifications_collection(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 4)

    response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualification_lots_ids = [q['lotID'] for q in qualifications]
    for bid in response.json['data']:
        response = self.app.get('/tenders/{}/bids/{}?acc_token={}'.format(self.tender_id, bid['id'], self.initial_bids_tokens[bid['id']]))
        for lotV in response.json['data']['lotValues']:
            lot_id = lotV['relatedLot']
            self.assertIn(lot_id, qualification_lots_ids)
            qualification_lots_ids.remove(lot_id)


def tender_qualification_cancelled(self):
    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']
    qualification_id = qualifications[0]['id']
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualification_id, self.tender_token),
                                   {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualification_id, self.tender_token),
                                   {"data": {"status": "active", "qualified": True, "eligible": True}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{"description": u"Can't update qualification in current cancelled qualification status",
                                                u'location': u'body', u'name': u'data'}])

    response = self.app.get('/tenders/{}/qualifications'.format(self.tender_id))
    self.assertEqual(response.content_type, 'application/json')

    new_qualifications = response.json['data']
    self.assertEqual(len(new_qualifications), 5)

# TenderQualificationDocumentResourceTest


def not_found(self):
    response = self.app.post('/tenders/some_id/qualifications/some_id/documents', status=404, upload_files=[
        ('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.post('/tenders/{}/qualifications/some_id/documents'.format(self.tender_id), status=404,
                             upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.post(
        '/tenders/{}/qualifications/{}/documents?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                      self.tender_token),
        status=404, upload_files=[('invalid_value', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.get('/tenders/some_id/qualifications/some_id/documents?acc_token={}'.format(self.tender_token),
                            status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get(
        '/tenders/{}/qualifications/some_id/documents?acc_token={}'.format(self.tender_id, self.tender_token),
        status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get(
        '/tenders/some_id/qualifications/some_id/documents/some_id?acc_token={}'.format(self.tender_token), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get(
        '/tenders/{}/qualifications/some_id/documents/some_id?acc_token={}'.format(self.tender_id, self.tender_token),
        status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/documents/some_id?acc_token={}'.format(self.tender_id,
                                                                                                  self.qualifications[
                                                                                                      0]['id'],
                                                                                                  self.tender_token),
                            status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'document_id'}
    ])

    response = self.app.put(
        '/tenders/some_id/qualifications/some_id/documents/some_id?acc_token={}'.format(self.tender_token), status=404,
        upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.put(
        '/tenders/{}/qualifications/some_id/documents/some_id?acc_token={}'.format(self.tender_id, self.tender_token),
        status=404, upload_files=[
            ('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/documents/some_id?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token), status=404,
        upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])

    self.app.authorization = ('Basic', ('invalid', ''))
    response = self.app.put('/tenders/{}/qualifications/{}/documents/some_id?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token), status=404,
        upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_qualification_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json["data"]["title"])
    key = response.json["data"]["url"].split('?')[-1]

    # qualifications are public
    response = self.app.get(
        '/tenders/{}/qualifications/{}/documents?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                      self.tender_token))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get(
        '/tenders/{}/qualifications/{}/documents?all=true'.format(self.tender_id, self.qualifications[0]['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?download=some_id'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?{}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 7)
    self.assertEqual(response.body, 'content')

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])


def put_qualification_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token),
        status=404, upload_files=[('invalid_name', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token),
        upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?{}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content2')

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    response = self.app.put('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token), 'content3',
        content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?{}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content3')

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        {'data': {"status": "active", "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')

    response = self.app.put('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token),
        upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u"Can't update document in current qualification status", u'location': u'body',
         u'name': u'data'}])


def patch_qualification_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                         doc_id, self.tender_token), {"data": {
            "documentOf": "lot"
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'relatedItem'},
    ])

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                         doc_id, self.tender_token), {"data": {
            "documentOf": "lot",
            "relatedItem": '0' * 32
        }}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'relatedItem should be one of lots'], u'location': u'body', u'name': u'relatedItem'}
    ])

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                         doc_id, self.tender_token),
        {"data": {"description": "document description"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])

    for qualification in self.qualifications:
        response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
            self.tender_id, qualification['id'], self.tender_token),
            {'data': {"status": "active", "qualified": True, "eligible": True}})
        self.assertEqual(response.status, '200 OK')

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                         doc_id, self.tender_token),
        {"data": {"description": "document description2"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')

    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data", "description": "Can't update document in current qualification status"}
    ])

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')

    response = self.app.patch_json(
        '/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualifications[0]['id'],
                                                                         doc_id, self.tender_token),
        {"data": {"description": "document description2"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')

    self.assertEqual(response.json['errors'], [
        {"location": "body", "name": "data",
         "description": "Can't update document in current (active.pre-qualification.stand-still) tender status"}
    ])


def create_qualification_document_after_status_change(self):
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        {'data': {"status": "active", "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u"Can't add document in current qualification status", u'location': u'body',
         u'name': u'data'}])

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[1]['id'], self.tender_token), {'data': {"status": "unsuccessful"}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[1]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u"Can't add document in current qualification status", u'location': u'body',
         u'name': u'data'}])

    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[1]['id'], self.tender_token), {'data': {"status": "cancelled"}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[1]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {u'description': u"Can't add document in current qualification status", u'location': u'body',
         u'name': u'data'}])
    response = self.app.get('/tenders/{}/qualifications?acc_token={}'.format(self.tender_id, self.tender_token))
    self.assertEqual(response.status, "200 OK")
    self.qualifications = response.json['data']
    self.assertEqual(len(self.qualifications), 3)
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[2]['id'], self.tender_token),
        {'data': {"status": "active", "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[2]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"description": u"Can't add document in current (active.pre-qualification.stand-still) tender status",
         u'location': u'body', u'name': u'data'}]
                     )


def put_qualification_document_after_status_change(self):
    response = self.app.post('/tenders/{}/qualifications/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], self.tender_token),
        upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    doc_id = response.json["data"]['id']
    for qualification in self.qualifications:
        response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(
            self.tender_id, qualification['id'], self.tender_token),
            {'data': {"status": "active", "qualified": True, "eligible": True}})
        self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')
    response = self.app.put('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token),
        upload_files=[('file', 'name.doc', 'content2')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [
        {"description": u"Can't update document in current (active.pre-qualification.stand-still) tender status",
         u'location': u'body', u'name': u'data'}])


def create_qualification_document_bot(self):
    self.app.authorization = ('Basic', ('bot', 'bot'))
    response = self.app.post('/tenders/{}/qualifications/{}/documents'.format(
        self.tender_id, self.qualifications[0]['id']), upload_files=[('file', 'edr_request.yaml','content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('edr_request.yaml', response.json["data"]["title"])
    if self.docservice:
        self.assertIn('Signature=', response.json["data"]["url"])
        self.assertIn('KeyID=', response.json["data"]["url"])
        self.assertNotIn('Expires=', response.json["data"]["url"])
        key = response.json["data"]["url"].split('/')[-1].split('?')[0]
        tender = self.db.get(self.tender_id)
        self.assertIn(key, tender['awards'][-1]['documents'][-1]["url"])
        self.assertIn('Signature=', tender['awards'][-1]['documents'][-1]["url"])
        self.assertIn('KeyID=', tender['awards'][-1]['documents'][-1]["url"])
        self.assertNotIn('Expires=', tender['awards'][-1]['documents'][-1]["url"])



def patch_document_not_author(self):
    authorization = self.app.authorization
    self.app.authorization = ('Basic', ('bot', 'bot'))

    response = self.app.post('/tenders/{}/qualifications/{}/documents'.format(self.tender_id, self.qualifications[0]['id']),
                             upload_files=[('file', 'edr_request.yaml', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    self.app.authorization = authorization
    response = self.app.patch_json('/tenders/{}/qualifications/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualifications[0]['id'], doc_id, self.tender_token),
        {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

# TenderQualificationComplaintResourceTest


def create_tender_qualification_complaint_invalid(self):
    response = self.app.post_json('/tenders/some_id/qualifications/some_id/complaints', {
                                  'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
    ])

    request_path = '/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0])

    response = self.app.post(request_path, 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description':
            u"Content-Type header should be one of ['application/json']", u'location': u'header', u'name': u'Content-Type'}
    ])

    response = self.app.post(
        request_path, 'data', content_type='application/json', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'No JSON object could be decoded',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(
        request_path, {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'author'},
        {u'description': [u'This field is required.'], u'location': u'body', u'name': u'title'},
    ])

    response = self.app.post_json(request_path, {'data': {
                                  'invalid_field': 'invalid_value'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Rogue field', u'location':
            u'body', u'name': u'invalid_field'}
    ])

    response = self.app.post_json(request_path, {
                                  'data': {'author': {'identifier': 'invalid_value'}}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'identifier': [
            u'Please use a mapping for this field or Identifier instance instead of unicode.']}, u'location': u'body', u'name': u'author'}
    ])

    response = self.app.post_json(request_path, {
                                  'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {'identifier': {'id': 0}}}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.']}, u'name': [u'This field is required.'], u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
    ])

    response = self.app.post_json(request_path, {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': {
        'name': 'name', 'identifier': {'uri': 'invalid_value'}}}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': {u'contactPoint': [u'This field is required.'], u'identifier': {u'scheme': [u'This field is required.'], u'id': [u'This field is required.'], u'uri': [u'Not a well formed URL.']}, u'address': [u'This field is required.']}, u'location': u'body', u'name': u'author'}
    ])


def create_tender_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    self.assertEqual(complaint['author']['name'], self.initial_bids[0]["tenderers"][0]['name'])
    self.assertIn('id', complaint)
    self.assertIn(complaint['id'], response.headers['Location'])

    self.set_status('unsuccessful')

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")


def patch_tender_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], self.tender_token), {"data": {
        "status": "cancelled",
        "cancellationReason": "reason"
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Forbidden")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "title": "claim title",
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["title"], "claim title")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "pending"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "pending")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "stopping",
        "cancellationReason": "reason"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "stopping")
    self.assertEqual(response.json['data']["cancellationReason"], "reason")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/some_id'.format(self.tender_id, self.qualification_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.patch_json('/tenders/some_id/qualifications/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "cancelled",
        "cancellationReason": "reason"
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint")

    response = self.app.patch_json('/tenders/{}/qualifications/some_id/complaints/some_id'.format(self.tender_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "stopping")
    self.assertEqual(response.json['data']["cancellationReason"], "reason")

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    self.set_status('complete')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "claim",
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) tender status")


def review_tender_qualification_complaint(self):
    for status in ['invalid', 'stopped', 'declined', 'satisfied']:
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_bids[0]["tenderers"][0],
            'status': 'pending'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']

        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
            "decision": '{} complaint'.format(status),
            'rejectReasonDescription': 'reject reason'
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["decision"], '{} complaint'.format(status))
        self.assertEqual(response.json['data']['rejectReasonDescription'], 'reject reason')

        if status in ['declined', 'satisfied']:
            response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
                "status": "accepted"
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["status"], "accepted")

            response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
                "decision": 'accepted:{} complaint'.format(status)
            }})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.json['data']["decision"], 'accepted:{} complaint'.format(status))

        response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
            "status": status
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["status"], status)


def review_tender_qualification_stopping_complaint(self):
    for status in ['stopped', 'declined', 'mistaken', 'invalid', 'satisfied']:
        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {
            'data': {
                'title': 'complaint title',
                'description': 'complaint description',
                'author': self.initial_bids[0]['tenderers'][0],
                'status': 'pending',
            }
        })
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        url_patch_complaint = '/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id'])
        response = self.app.patch_json('{}?acc_token={}'.format(url_patch_complaint, owner_token), {
            'data': {
                'status': 'stopping',
                'cancellationReason': 'reason',
            }
        })
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], 'stopping')
        self.assertEqual(response.json['data']['cancellationReason'], 'reason')

        self.app.authorization = ('Basic', ('reviewer', ''))
        response = self.app.patch_json(url_patch_complaint, {
            'data': {
                'decision': 'decision',
                'status': status,
            }
        })
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['status'], status)
        self.assertEqual(response.json['data']['decision'], 'decision')


def review_tender_award_claim(self):
    for status in ['invalid', 'resolved', 'declined']:
        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_bids[0]["tenderers"][0],
            'status': 'claim'
        }})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        complaint = response.json['data']
        complaint_token = response.json['access']['token']

        self.app.authorization = ('Basic', ('broker', ''))
        response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], self.tender_token), {"data": {
            "status": "answered",
            "resolutionType": status,
            "resolution": "resolution text for {} status".format(status)
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["resolutionType"], status)

        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], complaint_token), {"data": {
            "satisfied": 'i' in status,
        }})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']["satisfied"], 'i' in status)


def get_tender_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], complaint)

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/some_id'.format(self.tender_id, self.qualification_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])


def get_tender_qualification_complaints(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    response = self.app.get('/tenders/{}/qualifications/{}/complaints'.format(self.tender_id, self.qualification_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'][0], complaint)

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    tender = self.db.get(self.tender_id)
    tender['qualificationPeriod']['endDate'] = tender['qualificationPeriod']['startDate']
    self.db.save(tender)

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in qualificationPeriod")


def change_status_to_standstill_with_complaint(self):

    auth = self.app.authorization

    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    self.app.authorization = ('Basic', ('reviewer', ''))
    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "decision": '{} complaint'.format('accepted')
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["decision"], '{} complaint'.format('accepted'))

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "status": "accepted"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "accepted")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "decision": 'accepted:{} complaint'.format('accepted')
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["decision"], 'accepted:{} complaint'.format('accepted'))

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "status": "satisfied"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "satisfied")

    self.app.authorization = auth

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{"description": u"Can't switch to 'active.pre-qualification.stand-still' before resolve all complaints",
                                                u'location': u'body', u'name': u'data'}])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], self.tender_token), {"data": {
        "status": "resolved",
        "tendererAction": "Умови виправлено"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], 'resolved')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], 'active.pre-qualification.stand-still')

# TenderLotQualificationComplaintResourceTest


def create_tender_lot_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    self.assertEqual(complaint['author']['name'], self.initial_bids[0]["tenderers"][0]['name'])
    self.assertIn('id', complaint)
    self.assertIn(complaint['id'], response.headers['Location'])

    self.set_status('unsuccessful')

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add complaint in current (unsuccessful) tender status")


def patch_tender_lot_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0]
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "pending",
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "pending")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {"status": "stopping", "cancellationReason": "reason"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "stopping")
    self.assertEqual(response.json['data']["cancellationReason"], "reason")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/some_id'.format(self.tender_id, self.qualification_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.patch_json('/tenders/some_id/qualifications/some_id/complaints/some_id', {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "cancelled",
        "cancellationReason": "reason"
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint")

    response = self.app.patch_json('/tenders/{}/qualifications/some_id/complaints/some_id'.format(self.tender_id), {"data": {"status": "resolved", "resolution": "resolution text"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "stopping")
    self.assertEqual(response.json['data']["cancellationReason"], "reason")

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    self.set_status('complete')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "claim",
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update complaint in current (complete) tender status")


def get_tender_lot_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], complaint)

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/some_id'.format(self.tender_id, self.qualification_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])


def get_tender_lot_qualification_complaints(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    response = self.app.get('/tenders/{}/qualifications/{}/complaints'.format(self.tender_id, self.qualification_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'][0], complaint)

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    tender = self.db.get(self.tender_id)
    tender['qualificationPeriod']['endDate'] = tender['qualificationPeriod']['startDate']
    self.db.save(tender)

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in qualificationPeriod")

# Tender2LotQualificationComplaintResourceTest


def create_tender_2lot_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    self.assertEqual(complaint['author']['name'], self.initial_bids[0]["tenderers"][0]['name'])
    self.assertIn('id', complaint)
    self.assertIn(complaint['id'], response.headers['Location'])

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]),
                                  {'data': {'title': 'complaint title', 'description': 'complaint description', 'author': self.initial_bids[0]["tenderers"][0]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add complaint only in active lot status")


def patch_tender_2lot_qualification_complaint(self):
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0]
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "pending"
    }})

    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0]
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, complaint['id'], owner_token), {"data": {
        "status": "pending"
    }}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update complaint only in active lot status")


def change_status_to_standstill_with_complaint_cancel_lot(self):

    auth = self.app.authorization

    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.qualification_id, self.initial_bids_tokens.values()[0]), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    self.app.authorization = ('Basic', ('reviewer', ''))
    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "status": "accepted"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "accepted")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, self.qualification_id, complaint['id']), {"data": {
        "status": "satisfied"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "satisfied")

    self.app.authorization = auth

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], 'active.pre-qualification.stand-still')
    self.assertIn('next_check', response.json['data'])

    self.set_status('active.auction', {'status': 'active.pre-qualification.stand-still'})
    self.app.authorization = ('Basic', ('chronograph', ''))
    response = self.app.patch_json('/tenders/{}'.format(self.tender_id), {'data': {'id': self.tender_id}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], self.after_qualification_switch_to)

# Tender2LotQualificationClaimResourceTest


def create_tender_qualification_claim(self):
        response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.unsuccessful_qualification_id, self.initial_bids_tokens[self.initial_bids[0]['id']]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_bids[0]["tenderers"][0],
            'status': 'claim'
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Can add claim only on unsuccessful qualification of your bid', u'location': u'body', u'name': u'data'}
        ])

        response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, self.unsuccessful_qualification_id, self.initial_bids_tokens[self.initial_bids[0]['id']]), {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': self.initial_bids[0]["tenderers"][0],
            'status': 'draft'
        }})
        self.assertEqual(response.status, '201 Created')
        complaint = response.json['data']
        owner_token = response.json['access']['token']

        response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.unsuccessful_qualification_id, complaint['id'], owner_token), {"data": {
            "status": "claim",
        }}, status=403)
        self.assertEqual(response.status, '403 Forbidden')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['status'], 'error')
        self.assertEqual(response.json['errors'], [
            {u'description': u'Can add claim only on unsuccessful qualification of your bid', u'location': u'body', u'name': u'data'}
        ])

# TenderQualificationComplaintDocumentResourceTest


def complaint_not_found(self):
    response = self.app.post('/tenders/some_id/qualifications/some_id/complaints/some_id/documents', status=404, upload_files=[
                             ('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.post('/tenders/{}/qualifications/some_id/complaints/some_id/documents'.format(self.tender_id), status=404, upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/some_id/documents'.format(self.tender_id, self.qualification_id), status=404, upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), status=404, upload_files=[
                             ('invalid_value', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/some_id/complaints/some_id/documents'.format(self.tender_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/some_id/documents'.format(self.tender_id, self.qualification_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.get('/tenders/some_id/qualifications/some_id/complaints/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/some_id/complaints/some_id/documents/some_id'.format(self.tender_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/some_id/documents/some_id'.format(self.tender_id, self.qualification_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/some_id'.format(self.tender_id, self.qualification_id, self.complaint_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'document_id'}
    ])

    response = self.app.put('/tenders/some_id/qualifications/some_id/complaints/some_id/documents/some_id', status=404,
                            upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.put('/tenders/{}/qualifications/some_id/complaints/some_id/documents/some_id'.format(self.tender_id), status=404,
                            upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'qualification_id'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/some_id/documents/some_id'.format(self.tender_id, self.qualification_id), status=404, upload_files=[
                            ('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'complaint_id'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/some_id'.format(
        self.tender_id, self.qualification_id, self.complaint_id), status=404, upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_tender_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (draft) complaint status")

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json["data"]["title"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents'.format(self.tender_id, self.qualification_id, self.complaint_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents?all=true'.format(self.tender_id, self.qualification_id, self.complaint_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?download=some_id'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 7)
    self.assertEqual(response.body, 'content')

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    self.set_status('complete')

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (complete) tender status")


def put_tender_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token),
                            status=404,
                            upload_files=[('invalid_name', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content2')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content2')

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content3', content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content3')

    self.set_status('complete')

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")


def patch_tender_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.tender_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), {"data": {
        "status": "pending",
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "pending")

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content2', content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content2')

    self.set_status('complete')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current (complete) tender status")

# Tender2LotQualificationComplaintDocumentResourceTest


def create_tender_2lot_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current (draft) complaint status")

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json["data"]["title"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents'.format(self.tender_id, self.qualification_id, self.complaint_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents?all=true'.format(self.tender_id, self.qualification_id, self.complaint_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?download=some_id'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 7)
    self.assertEqual(response.body, 'content')

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")


def put_tender_2lot_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token),
                            status=404,
                            upload_files=[('invalid_name', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content2')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content2')

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content3', content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content3')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), {"data": {
        "status": "pending",
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "pending")

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), 'content4', content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content4')


    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.put('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


def patch_tender_2lot_qualification_complaint_document(self):
    response = self.app.post('/tenders/{}/qualifications/{}/complaints/{}/documents?acc_token={}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.tender_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only author")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/tenders/{}/qualifications/{}/complaints/{}/documents/{}'.format(
        self.tender_id, self.qualification_id, self.complaint_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, self.complaint_owner_token), {"data": {
        "status": "pending",
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']["status"], "pending")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description2"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["description"], "document description2")

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})
    self.assertEqual(response.status, '201 Created')

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}/documents/{}?acc_token={}'.format(self.tender_id, self.qualification_id, self.complaint_id, doc_id, self.complaint_owner_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")

def switch_bid_status_unsuccessul_to_active(self):
    bid_id, bid_token = self.initial_bids_tokens.items()[0]

    response = self.app.get('/tenders/{}/qualifications?acc_token={}'.format(self.tender_id, self.tender_token))
    self.assertEqual(response.content_type, 'application/json')
    qualifications = response.json['data']
    self.assertEqual(len(qualifications), 4)
    qualification_id = ""
    for qualification in qualifications:
        status = 'active'
        if qualification['bidID'] == bid_id:
            status = 'unsuccessful'
            qualification_id = qualification["id"]
        response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualification['id'], self.tender_token),
                                  {"data": {'status': status, "qualified": True, "eligible": True}})
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.json['data']['status'], status)
    response = self.app.patch_json('/tenders/{}?acc_token={}'.format(self.tender_id, self.tender_token),
                                   {"data": {"status": "active.pre-qualification.stand-still"}})
    self.assertEqual(response.status, "200 OK")

    # create complaint
    response = self.app.post_json('/tenders/{}/qualifications/{}/complaints?acc_token={}'.format(self.tender_id, qualification_id, bid_token), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': self.initial_bids[0]["tenderers"][0],
        'status': 'pending'
    }})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    complaint = response.json['data']

    self.app.authorization = ('Basic', ('reviewer', ''))
    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, qualification_id, complaint['id']), {"data": {
        "status": "accepted"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "accepted")

    response = self.app.patch_json('/tenders/{}/qualifications/{}/complaints/{}'.format(self.tender_id, qualification_id, complaint['id']), {"data": {
        "status": "satisfied"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "satisfied")

    # Cancell qualification
    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, qualification_id, self.tender_token),
                                   {"data": {'status': 'cancelled'}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'cancelled')

    new_qualification_id = response.headers['location'].split('/')[-1]
    response = self.app.patch_json('/tenders/{}/qualifications/{}?acc_token={}'.format(self.tender_id, new_qualification_id, self.tender_token),
                                   {"data": {'status': 'active', "qualified": True, "eligible": True}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')

    response = self.app.get('/tenders/{}/bids'.format(self.tender_id))
    for b in response.json['data']:
        self.assertEqual(b['status'], 'active')
