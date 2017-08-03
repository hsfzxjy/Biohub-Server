from rest_framework.test import APIClient
from django.test import TestCase
from biohub.accounts.models import User
from biohub.forum.models import Brick, Article, Experience
import json
# from time import sleep


class BrickRestfulAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(username="abc")
        self.user.set_password("123456000+")
        self.user.save()
        self.document =  Article.objects.create(text='aaa')
        self.brick = Brick.objects.create(name='K314110', group_name='well',
                                          document=self.document)

    def test_checking_whether_database_has_brick(self):
        response = self.client.get('/api/forum/bricks/check_database/?name=ADD')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/api/forum/bricks/check_database/')
        self.assertEqual(response.status_code, 400)
        brick = Brick.objects.create(name='lalala')
        response = self.client.get('/api/forum/bricks/check_database/?name=lalala')
        self.assertEqual(response.status_code, 200)

    def test_checking_whether_igem_has_brick(self):
        response = self.client.get('/api/forum/bricks/check_igem/?name=ADD')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/api/forum/bricks/check_igem/')
        self.assertEqual(response.status_code, 400)
        response = self.client.get('/api/forum/bricks/check_igem/?name=K314110')
        self.assertEqual(response.status_code, 200)

    # def test_automatically_update_bricks_when_retrieving(self):
    #     brick = Brick.objects.get(name='K314110')
    #     brick.group_name = 'emmm'
    #     brick.save()
    #     # Because auto_now is set to True in Brick model, update_time is impossible to be set manually.
    #     # To use this test, please set UPDATE_DELTA = datetime.timedelta(seconds=1) in views.
    #     sleep(5)
    #     response = self.client.get('/api/forum/bricks/%d/' % brick.id)
    #     sleep(5)
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.content)
    #     self.assertEqual(data['group_name'], 'iGEM10_Washington')
    #     brick = Brick.objects.create(name='a')
    #     response = self.client.get('/api/forum/bricks/%d/' % brick.id)
    #     self.assertEqual(response.status_code, 500)

    def test_list_data_with_and_without_param_short(self):
        response = self.client.get('/api/forum/bricks/')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['results'][0]['group_name'], 'well')
        response = self.client.get('/api/forum/bricks/?short=true')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        group_name = data['results'][0].get('group_name', None)
        self.assertEqual(group_name, None)

    def test_unable_to_upload_brick(self):
        self.client.login(username='abc', password='123456000+')
        response = self.client.post('/api/forum/bricks/', {
            'name': 'haha'
        })
        self.assertEqual(response.status_code, 405)

    # def test_visiting_igem_fails_returns_500(self):
    #     # Note: Run this test without network and
    #     # comment test_checking_whether_igem_has_brick test at the same time.
    #     response = self.client.get('/api/forum/bricks/check_igem/?name=K314110')
    #     self.assertEqual(response.status_code, 500)

    def test_fetch_experiences_of_particular_brick(self):
        Experience.objects.create(title='ha', brick=self.brick, author=self.user)
        Experience.objects.create(title='emmmm', brick=self.brick)
        response = self.client.get('/api/forum/bricks/%d/experiences/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 2)
        response = self.client.get('/api/forum/bricks/%d/experiences/?author=%s'
                                   % (self.brick.id, self.user.username))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'ha')
        # test short=true
        response = self.client.get('/api/forum/bricks/%d/experiences/?author=%s&short=true'
                                   % (self.brick.id, self.user.username))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertIs('pub_time' in data['results'][0], False)
        # test: can not post experiences
        self.assertEqual(self.client.login(username='abc', password='123456000+'), True)
        response = self.client.post('/api/forum/bricks/%d/experiences/' % self.brick.id, {})
        self.assertEqual(response.status_code, 405)
