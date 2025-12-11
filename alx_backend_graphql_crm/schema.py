# alx_backend_graphql_crm/schema.py
import graphene

# Define the root Query class for your GraphQL API
class Query(graphene.ObjectType):
    # 1. Declare a field named 'hello'
    # 2. Set its type to String (graphene.String)
    hello = graphene.String()

    # 3. Define the resolver method for the 'hello' field
    #    The method must be named 'resolve_[field_name]'
    def resolve_hello(root, info):
        return "Hello, GraphQL!"

# Combine the Query class into an executable Schema
schema = graphene.Schema(query=Query)