import graphene

import simple_app.schema


class Queries(
    simple_app.schema.Query,
    graphene.ObjectType
):
    dummy = graphene.String()


schema = graphene.Schema(query=Queries)
