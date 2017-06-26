import json
import graphene
from graphene_django.types import DjangoObjectType

from . import models


class MessageType(DjangoObjectType):
    class Meta:
        model = models.Message


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
    message = graphene.Field(MessageType, id=graphene.Int())

    def resolve_message(self, args, context, info):
        return models.Message.objects.get(pk=args.get('id'))

    all_messages = graphene.List(MessageType)

    def resolve_all_messages(self, args, context, info):
        return models.Message.objects.all()
