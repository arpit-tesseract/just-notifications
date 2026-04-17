from configuration.models import Dimension, Level, Node
from .models import User, UserPersonalDetails, RelationType, UserRelations

def get_level_node_mapping(node_json):
    if not node_json:
        return {}

    for level_id, node_id in node_json.items():
        try:
            node_obj = Node.objects.get(id=node_id, level_id=level_id)
            node_json[level_id] = {
                "id": node_obj.id,
                "name": node_obj.name
            }
        except Node.DoesNotExist:
            node_json[level_id] = None
    
    return node_json


def get_pidhi_node_from_personal_details(personal_details_obj):
    if not personal_details_obj:
        return None
    
    try:
        dimension_obj = Dimension.objects.get(name="Personal")
        pidhi_level_obj = Level.objects.get(name="pidhi", dimension=dimension_obj)
    except (Dimension.DoesNotExist, Level.DoesNotExist):
        return None


    node_data = personal_details_obj.nodes
    if not node_data:
        return None
    
    pidhi_level_key = str(pidhi_level_obj.id)
    node_id = node_data.get(pidhi_level_key)
    if not node_id:
        return None
    
    try:
        node_obj = Node.objects.get(id=node_id)
    except Node.DoesNotExist:
        return None

    return node_obj


def map_family_internal_relations(users):
    husbands = [user for user in users if user.get("self_relation_type").name == "husband"]
    wifes = [user for user in users if user.get("self_relation_type").name == "wife"]
    sons = [user for user in users if user.get("self_relation_type").name == "son"]
    daughters = [user for user in users if user.get("self_relation_type").name == "daughter"]
    guests = [user for user in users if user.get("self_relation_type").name == "guest"]
    workers = [user for user in users if user.get("self_relation_type").name == "workers"]

    relation_types_qs = RelationType.objects.filter(is_active=True)

    if husbands and wifes:
        for husband in husbands:
            for wife in wifes:
                # Create husband to wife relation
                UserRelations.objects.get_or_create(
                    from_user=husband.get("user"),
                    relation_type=relation_types_qs.get(name="husband"),
                    to_user=wife.get("user")
                )
                # Create wife to husband relation
                UserRelations.objects.get_or_create(
                    from_user=wife.get("user"),
                    relation_type=relation_types_qs.get(name="wife"),
                    to_user=husband.get("user")
                )

    if husbands and sons:
        for husband in husbands:
            for son in sons:
                # Create father to son relation
                UserRelations.objects.get_or_create(
                    from_user=husband.get("user"),
                    relation_type=relation_types_qs.get(name="father"),
                    to_user=son.get("user")
                )
                # Create son to father relation
                UserRelations.objects.get_or_create(
                    from_user=son.get("user"),
                    relation_type=relation_types_qs.get(name="son"),
                    to_user=husband.get("user")
                )  

    if husbands and daughters:
        for husband in husbands:
            for daughter in daughters:
                # Create father to daughter relation     
                UserRelations.objects.get_or_create(
                    from_user=husband.get("user"),
                    relation_type=relation_types_qs.get(name="father"),
                    to_user=daughter.get("user")
                )
                # Create daughter to father relation
                UserRelations.objects.get_or_create(
                    from_user=daughter.get("user"),
                    relation_type=relation_types_qs.get(name="daughter"),
                    to_user=husband.get("user")
                )
    
    if wifes and sons:
        for wife in wifes:
            for son in sons:
                # Create mother to son relation
                UserRelations.objects.get_or_create(
                    from_user=wife.get("user"),
                    relation_type=relation_types_qs.get(name="mother"),
                    to_user=son.get("user")
                )
                # Create son to mother relation
                UserRelations.objects.get_or_create(
                    from_user=son.get("user"),
                    relation_type=relation_types_qs.get(name="son"),
                    to_user=wife.get("user")
                )

    if wifes and daughters:
        for wife in wifes:
            for daughter in daughters:
                # Create mother to daughter relation
                UserRelations.objects.get_or_create(
                    from_user=wife.get("user"),
                    relation_type=relation_types_qs.get(name="mother"),
                    to_user=daughter.get("user")
                )
                # Create daughter to mother relation
                UserRelations.objects.get_or_create(
                    from_user=daughter.get("user"),
                    relation_type=relation_types_qs.get(name="daughter"),
                    to_user=wife.get("user")
                )
    
    if sons and daughters:
        for son in sons:
            for daughter in daughters:
                # Create son to daughter relation
                UserRelations.objects.get_or_create(
                    from_user=son.get("user"),
                    relation_type=relation_types_qs.get(name="brother"),
                    to_user=daughter.get("user")
                )
                # Create daughter to son relation
                UserRelations.objects.get_or_create(
                    from_user=daughter.get("user"),
                    relation_type=relation_types_qs.get(name="sister"),
                    to_user=son.get("user")
                )
    
    if len(sons) > 1:
        for son in sons:
            for next_son in sons[sons.index(son)+1:]:
                # Create son to next son relation
                UserRelations.objects.get_or_create(
                    from_user=son.get("user"),
                    relation_type=relation_types_qs.get(name="brother"),
                    to_user=next_son.get("user")
                )
                # Create next son to son relation
                UserRelations.objects.get_or_create(
                    from_user=next_son.get("user"),
                    relation_type=relation_types_qs.get(name="brother"),
                    to_user=son.get("user")
                )
    
    if len(daughters) > 1:
        for daughter in daughters:
            for next_daughter in daughters[daughters.index(daughter)+1:]:
                # Create daughter to next daughter relation
                UserRelations.objects.get_or_create(
                    from_user=daughter.get("user"),
                    relation_type=relation_types_qs.get(name="sister"),
                    to_user=next_daughter.get("user")
                )
                # Create next daughter to daughter relation
                UserRelations.objects.get_or_create(
                    from_user=next_daughter.get("user"),
                    relation_type=relation_types_qs.get(name="sister"),
                    to_user=daughter.get("user")
                )
    
    if husbands and guests:
        for husband in husbands:
            for guest in guests:
                # Create husband to guest relation
                relation_type_obj = guest.get("relation")
                if relation_type_obj:
                    UserRelations.objects.get_or_create(
                        from_user=husband.get("user"),
                        relation_type=relation_type_obj,
                        to_user=guest.get("user")
                    )

    
    if husbands and workers:
        for husband in husbands:
            for worker in workers:
                # Create husband to worker relation
                relation_type_obj = worker.get("relation")
                if relation_type_obj:
                    UserRelations.objects.get_or_create(
                        from_user=husband.get("user"),
                        relation_type=relation_type_obj,
                        to_user=worker.get("user")
                    )


def map_relations_with_husband_user(registration_family_obj, users):
    registration_husband_user = registration_family_obj.members.filter(self_relation_type__name="husband").first().user
    for user in users:
        relation_type_objs = user.get("relation")
        if relation_type_objs:
            for relation in relation_type_objs:
                UserRelations.objects.get_or_create(
                    from_user=user.get("user"),
                    relation_type=relation,
                    to_user=registration_husband_user
                )