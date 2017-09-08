import re
import logging
import datetime
import requests

from django.utils import timezone
from django.db.models.query import QuerySet
from rest_framework import viewsets, status, decorators, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.exceptions import APIException, NotFound

from biohub.utils.rest import pagination, permissions
from biohub.accounts.models import User
from biohub.accounts.mixins import UserPaginationMixin, BaseUserViewSetMixin

from ..serializers import BrickSerializer
from ..models import Brick
from ..spiders import BrickSpider, ExperienceSpider

logger = logging.getLogger(__name__)


class BaseBrickViewSet(object):

    serializer_class = BrickSerializer
    pagination_class = pagination.factory('PageNumberPagination')
    queryset = Brick.objects.all().order_by('name')


class BrickViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   UserPaginationMixin,
                   BaseBrickViewSet,
                   viewsets.GenericViewSet):

    brick_spider = BrickSpider()
    experience_spider = ExperienceSpider()
    UPDATE_DELTA = datetime.timedelta(days=10)

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        Override this function to provide "request" as None.
        """
        return {
            'request': None,
            'format': self.format_kwarg,
            'view': self
        }

    @staticmethod
    def has_brick_in_database(brick_name):
        return Brick.objects.filter(name=brick_name).exists()

    @staticmethod
    def has_brick_in_igem(brick_name):
        url = 'http://parts.igem.org/cgi/xml/part.cgi?part=BBa_' + brick_name
        try:
            raw_data = requests.get(url).text
        except Exception as e:
            logger.error('Unable to visit url:' + url)
            logger.error(e)
            raise APIException
        return re.search(
            r'(?i)<ERROR>Part name not found.*</ERROR>|'
            r'<\s*part_list\s*/\s*>|'
            r'<\s*part_list\s*>\s*<\s*/\s*part_list\s*>',
            raw_data
        ) is None

    @staticmethod
    def update_brick(brick_name, brick):
        try:
            BrickViewSet.brick_spider.fill_from_page(brick_name, brick=brick)
            BrickViewSet.experience_spider.fill_from_page(brick_name)
        except Exception as e:
            raise e

    def check_database(self, *args, **kwargs):
        brick_name = self.request.query_params.get('name', None)
        if brick_name is not None:
            if BrickViewSet.has_brick_in_database(brick_name):
                return Response('Database has it.', status=status.HTTP_200_OK)
            return Response('Database does not have it', status=status.HTTP_404_NOT_FOUND)
        return Response('Must specify param \'name\'.', status=status.HTTP_400_BAD_REQUEST)

    def check_igem(self, *args, **kwargs):
        brick_name = self.request.query_params.get('name', None)
        if brick_name is not None:
            if BrickViewSet.has_brick_in_igem(brick_name):
                return Response('iGEM has it.', status=status.HTTP_200_OK)
            return Response('iGEM does not have it', status=status.HTTP_404_NOT_FOUND)
        return Response('Must specify param \'name\'.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['GET'])
    def watched_users(self, *args, **kwargs):
        return self.paginate_user_queryset(self.get_object().watch_users.all())

    @decorators.detail_route(methods=['GET'])
    def rated_users(self, *args, **kwargs):
        return self.paginate_user_queryset(self.get_object().rate_users.all())

    @decorators.detail_route(methods=['GET'])
    def starred_users(self, *args, **kwargs):
        return self.paginate_user_queryset(self.get_object().star_users.all())

    @decorators.detail_route(methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def watch(self, *args, **kwargs):
        if self.get_object().watch(self.request.user):
            return Response('OK')
        return Response('Fail.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def cancel_watch(self, *args, **kwargs):
        if self.get_object().cancel_watch(self.request.user):
            return Response('OK')
        return Response('Fail.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def rate(self, request, *args, **kwargs):
        score = request.data.get('score', None)
        if score is None:
            return Response(
                'Must upload your rating score.',
                status=status.HTTP_400_BAD_REQUEST
            )
        if self.get_object().rate(score, self.request.user):
            return Response('OK')
        return Response('Fail.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def star(self, request, *args, **kwargs):
        if self.get_object().star(self.request.user):
            return Response('OK')
        return Response('Fail.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def unstar(self, request, *args, **kwargs):
        if self.get_object().unstar(self.request.user):
            return Response('OK')
        return Response('Fail.', status=status.HTTP_400_BAD_REQUEST)

    @decorators.list_route(methods=['GET'])
    def watched_bricks(self, request, *args, **kwargs):
        username = self.request.query_params.get('username', None)
        if username is not None:
            queryset = User.objects.get(
                username=username).bricks_watched.all().order_by('name', 'id')
            short = self.request.query_params.get('short', None)
            page = self.paginate_queryset(queryset)
            if short is not None and short.lower() == 'true':
                serializer = BrickSerializer(
                    page,
                    fields=('api_url', 'id', 'name'),
                    many=True,
                    context={
                        'request': None
                    }
                )
                return self.get_paginated_response(serializer.data)
            serializer = BrickSerializer(page, many=True, context={
                'request': None
            })
            return self.get_paginated_response(serializer.data)
        return Response("Must specify param 'username'.", status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        brick = self.get_object()
        now = timezone.now()
        if now - brick.update_time > self.UPDATE_DELTA:
            try:
                self.update_brick(brick_name=brick.name, brick=brick)
                brick = self.get_object()
            except Exception as e:
                if e.args == 'The part does not exist on iGEM\'s website':
                    return Response('Unable to find this brick! ' + str(e),
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response('Unable to fetch data of this brick! ',
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = BrickSerializer(brick, context={
            'request': None
        })
        return Response(serializer.data)

    def get_queryset(self):
        ''' enable searching via URL parameter: 'name', not including 'BBa_' '''
        name_begin_with = self.request.query_params.get('name', None)
        if name_begin_with:
            return Brick.objects.filter(name__icontains=name_begin_with).order_by('name')
        else:
            # from REST framework's src code:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                # Ensure queryset is re-evaluated on each request.
                queryset = queryset.all()
            return queryset

    def list(self, request, *args, **kwargs):
        short = self.request.query_params.get('short', None)
        if short is not None and short.lower() == 'true':
            page = self.paginate_queryset(self.get_queryset())
            serializer = BrickSerializer(page, fields=('api_url', 'id', 'name'), many=True, context={
                'request': None
            })
            return self.get_paginated_response(serializer.data)
        return super(BrickViewSet, self).list(request=request, *args, **kwargs)


class UserBrickViewSet(mixins.ListModelMixin, BaseBrickViewSet, BaseUserViewSetMixin):

    allowed_actions = {
        'watched_bricks': 'bricks_watched',
        'starred_bricks': 'bricks_starred',
        'rated_bricks': 'bricks_rated'
    }

    def get_queryset(self):
        try:
            return getattr(self.get_user_object(), self.allowed_actions[self.action]).order_by('name')
        except KeyError:
            raise NotFound

    @decorators.list_route(methods=['GET'])
    def watched_bricks(self, *args, **kwargs):
        return self.list(*args, **kwargs)

    @decorators.list_route(methods=['GET'])
    def starred_bricks(self, *args, **kwargs):
        return self.list(*args, **kwargs)

    @decorators.list_route(methods=['GET'])
    def rated_bricks(self, *args, **kwargs):
        return self.list(*args, **kwargs)


@api_view(['GET'])
def retrieve_brick_by_name(request, brick_name):
    # use try except directly rather than check_database() method to avoid query the database twice.
    try:
        brick = Brick.objects.get(name=brick_name)
    except Brick.DoesNotExist:
        try:
            BrickViewSet.update_brick(brick_name=brick_name, brick=None)
        except Exception as e:
            if e.args == 'The part does not exist on iGEM\'s website':
                return Response('Unable to find this brick! ' + e.args,
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Unable to fetch data of this brick or of the experiences.',
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        brick = Brick.objects.get(name=brick_name)
    serializer = BrickSerializer(brick, context={
        'request': None
    })
    return Response(serializer.data)
