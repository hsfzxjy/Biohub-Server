from rest_framework import serializers
from biohub.utils.rest.serializers import bind_model,\
    ModelSerializer
from ..models import Brick
from biohub.accounts.serializers import UserSerializer


@bind_model(Brick)
class BrickSerializer(ModelSerializer):
    document = serializers.HyperlinkedRelatedField(view_name='api:forum:article-detail', read_only=True)
    followers = UserSerializer(fields=('id', 'username'), read_only=True, many=True)

    class Meta:
        model = Brick
        exclude = ('update_time',)
        read_only_fields = ('id', 'name', 'is_part', 'designer', 'group_name', 'part_type',
                            'nickname', 'part_status', 'sample_status', 'experience_status',
                            'use_num', 'twin_num', 'document', 'dna_position', 'followers',
                            'assembly_compatibility', 'parameters', 'categories',
                            'sequence_a', 'sequence_b', 'used_by', 'sub_parts')