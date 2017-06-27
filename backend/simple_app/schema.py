import json
import graphene
from django.contrib.auth.models import User
from graphene_django.types import DjangoObjectType
from graphene_django.filter.fields import DjangoFilterConnectionField

from . import models


class UserType(DjangoObjectType):
    class Meta:
        model = User


class MessageType(DjangoObjectType):
    class Meta:
        model = models.Message
        filter_fields = {'message': ['icontains']}
        interfaces = (graphene.Node, )


class CreateMessageMutation(graphene.Mutation):
    class Input:
        message = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    message = graphene.Field(MessageType)

    @staticmethod
    def mutate(root, args, context, info):
        if not context.user.is_authenticated():
            return CreateMessageMutation(status=403)
        message = args.get('message', '').strip()
        if not message:
            return CreateMessageMutation(
                status=400,
                formErrors=json.dumps(
                    {'message': ['Please enter a message.']}))
        obj = models.Message.objects.create(
            user=context.user, message=message
        )
        return CreateMessageMutation(status=200, message=obj)


class Mutation(graphene.AbstractType):
    create_message = CreateMessageMutation.Field()


class Query(graphene.AbstractType):
    current_user = graphene.Field(UserType)

    def resolve_current_user(self, args, context, info):
        if not context.user.is_authenticated():
            return None
        return context.user

    message = graphene.Field(MessageType, id=graphene.Int())

    def resolve_message(self, args, context, info):
        return models.Message.objects.get(pk=args.get('id'))

    all_messages = DjangoFilterConnectionField(MessageType)

    def resolve_all_messages(self, args, context, info):
        return models.Message.objects.all()
