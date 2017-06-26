import graphene
from graphene_django.types import DjangoObjectType

from . import models


class MessageType(DjangoObjectType):
    class Meta:
        model = models.Message


class Query(graphene.AbstractType):
    message = graphene.Field(MessageType, id=graphene.Int())

    def resolve_message(self, args, context, info):
        return models.Message.objects.get(pk=args.get('id'))

    all_messages = graphene.List(MessageType)
    
    def resolve_all_messages(self, args, context, info):
        return models.Message.objects.all()
