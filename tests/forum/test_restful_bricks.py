from rest_framework.test import APIClient
from django.test import TestCase
from biohub.accounts.models import User
from biohub.forum.models import Brick, Article, Experience


class BrickRestfulAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_test_user(username="abc")
        self.user.set_password("123456000+")
        self.user.save()
        self.document = Article.objects.create(text='aaa')
        self.brick = Brick.objects.create(name='K314110', group_name='well',
                                          document=self.document)

    def test_list_data_with_and_without_param_short(self):
        response = self.client.get('/api/forum/bricks/')
        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['results'][0]['group_name'], 'well')
        response = self.client.get('/api/forum/bricks/?short=true')
        data = response.data
        self.assertEqual(response.status_code, 200)
        group_name = data['results'][0].get('group_name', None)
        self.assertIsNone(group_name)

    def test_unable_to_upload_brick(self):
        self.client.login(username='abc', password='123456000+')
        response = self.client.post('/api/forum/bricks/', {
            'name': 'haha'
        })
        self.assertEqual(response.status_code, 405)

    def test_fetch_experiences_of_particular_brick(self):
        brick = Brick.objects.create(name='test')
        Experience.objects.create(title='ha', brick=brick, author=self.user)
        Experience.objects.create(title='emmmm', brick=brick)
        b = Brick.objects.create(name='a')
        Experience.objects.create(title='e', brick=b)
        response = self.client.get('/api/forum/bricks/%d/experiences/' % brick.id)
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['results']), 2)
        response = self.client.get('/api/forum/bricks/%d/experiences/?author=%s'
                                   % (brick.id, self.user.username))
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'ha')
        # test short=true
        response = self.client.get('/api/forum/bricks/%d/experiences/?author=%s&short=true'
                                   % (brick.id, self.user.username))
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data['results']), 1)
        self.assertFalse('pub_time' in data['results'][0])
        # test: can not post experiences
        self.assertEqual(self.client.login(username='abc', password='123456000+'), True)
        response = self.client.post('/api/forum/bricks/%d/experiences/' % brick.id, {})
        self.assertEqual(response.status_code, 405)

    def test_using_name_rather_than_id_to_retrieve_brick(self):
        response = self.client.get('/api/forum/bricks/I718017/')
        self.assertEqual(response.status_code, 200)
        # with open("brick_content.txt",'wb') as f:
        #     f.write(response.content)
        data = response.data
        self.assertEqual(data['group_name'], 'iGEM07_Paris')
        experience_url = data['experience_set'][0]
        response = self.client.get(experience_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['author_name'], 'igem2010 UT-Tokyo ')

    def test_retrieve_using_id(self):
        response = self.client.get('/api/forum/bricks/%d/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['group_name'], 'well')

    def test_list_using_searching_param(self):
        # fetch several bricks
        response = self.client.get('/api/forum/bricks/I6101/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/forum/bricks/E0240/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/forum/bricks/I742158/')
        self.assertEqual(response.status_code, 200)
        # list all bricks
        response = self.client.get('/api/forum/bricks/')
        # there ought to be 4 items, including the one in setUp()
        # search bricks beginning with 'I'
        self.assertEqual(len(response.data['results']), 4)
        response = self.client.get('/api/forum/bricks/?name=I')
        # there ought to be 2 items
        self.assertEqual(len(response.data['results']), 2)

    def test_star(self):
        self.assertEqual(self.brick.star_users.all().count(), 0)
        response = self.client.post('/api/forum/bricks/%d/star/' % self.brick.id)
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/forum/bricks/%d/star/' % self.brick.id)
        self.assertEqual(
            self.client.get('/api/forum/bricks/%d/starred_users/' % self.brick.id).data['count'],
            1
        )
        self.assertEqual(self.client.get('/api/users/me/starred_bricks/').data['count'], 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.brick.star_users.filter(pk=self.user.id).count(), 1)
        self.brick.refresh_from_db()
        self.assertEqual(self.brick.stars, 1)

    def test_unstar(self):
        self.test_star()
        response = self.client.post('/api/forum/bricks/%d/unstar/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.brick.star_users.filter(pk=self.user.id).count(), 0)
        self.brick.refresh_from_db()
        self.assertEqual(self.brick.stars, 0)
        self.assertEqual(self.client.get('/api/users/me/starred_bricks/').data['count'], 0)

    def test_watch_a_brick(self):
        self.assertEqual(self.brick.watch_users.all().count(), 0)
        response = self.client.post('/api/forum/bricks/%d/watch/' % self.brick.id)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username='abc', password='123456000+'))
        response = self.client.post('/api/forum/bricks/%d/watch/' % self.brick.id)
        self.assertEqual(
            self.client.get('/api/forum/bricks/%d/watched_users/' % self.brick.id).data['count'],
            1
        )
        self.assertEqual(self.client.get('/api/users/me/watched_bricks/').data['count'], 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.brick.watch_users.all().count(), 1)

    def test_cancel_watch_a_brick(self):
        self.assertTrue(self.brick.watch(self.user))
        self.assertEqual(self.brick.watch_users.all().count(), 1)
        response = self.client.post('/api/forum/bricks/%d/cancel_watch/' % self.brick.id)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username='abc', password='123456000+'))
        response = self.client.post('/api/forum/bricks/%d/cancel_watch/' % self.brick.id)
        self.assertEqual(self.client.get('/api/users/me/watched_bricks/').data['count'], 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.brick.watch_users.all().count(), 0)

    def test_api_url_field(self):
        response = self.client.get('/api/forum/bricks/%d/' % self.brick.id)
        self.assertEqual(response.data['api_url'], '/api/forum/bricks/%d/' % self.brick.id)

    def test_rate(self):
        user2 = User.objects.create_test_user(username="fff")
        user2.set_password("1593562120")
        user2.save()
        response = self.client.get('/api/forum/bricks/%d/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rate_score'], '0.0')
        response = self.client.post('/api/forum/bricks/%d/rate/' % self.brick.id)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.client.login(username='fff', password='1593562120'))
        response = self.client.post('/api/forum/bricks/%d/rate/' % self.brick.id)
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/forum/bricks/%d/rate/' % self.brick.id, {
            'score': 3
        })
        self.assertEqual(
            self.client.get('/api/forum/bricks/%d/rated_users/' % self.brick.id).data['count'], 1
        )
        self.assertEqual(self.client.get('/api/users/me/rated_bricks/').data['count'], 1)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/forum/bricks/%d/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rate_score'], '3.0')
        response = self.client.post('/api/forum/bricks/%d/rate/' % self.brick.id, {
            'score': 4
        })
        self.assertEqual(response.status_code, 400)
        user3 = User.objects.create_test_user(username='bbb')
        user3.set_password('1010101010')
        user3.save()
        self.assertTrue(self.client.login(username='bbb', password='1010101010'))
        response = self.client.post('/api/forum/bricks/%d/rate/' % self.brick.id, {
            'score': 4
        })
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/forum/bricks/%d/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['rate_score'], '3.5')

    def test_getting_bricks_watched(self):
        response = self.client.get('/api/forum/bricks/watched_bricks/')
        self.assertEqual(response.status_code, 400)
        response = self.client.get('/api/forum/bricks/watched_bricks/?username=abc')
        self.assertEqual(len(response.data['results']), 0)
        self.assertTrue(self.client.login(username='abc', password='123456000+'))
        response = self.client.post('/api/forum/bricks/%d/watch/' % self.brick.id)
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/api/forum/bricks/watched_bricks/?username=abc')
        data = response.data
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['id'], self.brick.id)
        response = self.client.get('/api/forum/bricks/watched_bricks/?username=abc')
        data = response.data
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['id'], self.brick.id)
        response = self.client.get('/api/forum/bricks/watched_bricks/?username=abc&short=true')
        data = response.data
        self.assertNotIn('designer', data['results'][0])
