import graphene


class Queries(
    graphene.ObjectType
):
    dummy = graphene.String()


schema = graphene.Schema(query=Queries)
