import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

# Combine the Query classes
class Query(CRMQuery, graphene.ObjectType):
    # This inherits all fields from CRMQuery (hello, customer, all_customers)
    pass

# Combine the Mutation classes
class Mutation(CRMMutation, graphene.ObjectType):
    # This inherits all fields from CRMMutation (create_customer, etc.)
    pass

# Define the final executable schema
schema = graphene.Schema(query=Query, mutation=Mutation)