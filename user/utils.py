from configuration.models import Dimension, Level, Node
from .models import User, UserPersonalDetails, RelationType, UserRelations, Family, FamilyMember

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


from .models import UserRelations

def build_family_tree(user):
    spouse = UserRelations.objects.filter(
        to_user=user,
        relation_type__name__in=["husband", "wife"]
    ).select_related("to_user").first()

    children = UserRelations.objects.filter(
        to_user=user,
        relation_type__name__in=["son", "daughter"]
    ).select_related("to_user")

    father = UserRelations.objects.filter(
        to_user=user,
        relation_type__name="father"
    ).select_related("to_user").first()

    mother = UserRelations.objects.filter(
        to_user=user,
        relation_type__name="mother"
    ).select_related("to_user").first()

    siblings = UserRelations.objects.filter(
        to_user=user,
        relation_type__name__in=["brother", "sister"]
    ).select_related("to_user")

    return {
        "id": user.id,
        "name": user.full_name,

        "spouse": {
            "id": spouse.to_user.id,
            "name": spouse.to_user.full_name,
            "relation": spouse.relation_type.name
        },

        "children": [
            {
                "id": c.from_user.id,
                "name": c.from_user.full_name,
                "relation": c.relation_type.name
            } for c in children
        ],

        "parents": {
            "father": {
                "id": father.to_user.id,
                "name": father.to_user.full_name
            },
            "mother": {
                "id": mother.to_user.id,
                "name": mother.to_user.full_name
            }
        },

        "siblings": [
            {
                "id": s.from_user.id,
                "name": s.from_user.full_name,
                "relation": s.relation_type.name
            } for s in siblings
        ]
    }


# utils.py

import re
from collections import defaultdict, deque

from django.db.models import Q

from .models import (
    Family,
    FamilyMember,
    User,
    UserRelations,
)

from .utils import get_pidhi_node_from_personal_details


# ---------------------------------------------------------
# Helper: Extract number from Pidhi-1 / pidhi-2 / Pidhi 10
# ---------------------------------------------------------
def extract_pidhi(value):
    if not value:
        return 9999

    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 9999


# ---------------------------------------------------------
# Helper: Get pidhi from user.personal_details
# ---------------------------------------------------------
def get_user_pidhi(user):
    personal = getattr(user, "personal_details", None)

    pidhi_node = get_pidhi_node_from_personal_details(personal)

    if not pidhi_node:
        return 9999

    return extract_pidhi(pidhi_node.name)


# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------
def build_family_tree_by_pidhi(family_id):
    """
    Full production family tree.

    Starts from current family members,
    then expands using UserRelations graph,
    then groups all persons by pidhi.

    Output:
    {
        family_id,
        family_type,
        main_user_id,
        generations: {
            "1": [...],
            "2": [...]
        },
        edges: [
            {"from":1,"to":2,"relation":"father"}
        ]
    }
    """

    # -------------------------------------------------
    # Load current family
    # -------------------------------------------------
    family = Family.objects.prefetch_related(
        "members__user__profile",
        "members__user__personal_details",
        "residents__residential_type",
    ).get(id=family_id)

    family_type = None
    resident = family.residents.first()
    if resident:
        family_type = resident.residential_type.name

    members = family.members.all()
    print("Members: ", members)
    # -------------------------------------------------
    # Base users = current family members
    # -------------------------------------------------
    start_user_ids = set(member.user_id for member in members)

    # main user
    main_user_id = None
    for member in members:
        if member.is_main_user:
            main_user_id = member.user_id
            break

    # -------------------------------------------------
    # BFS Traversal through UserRelations
    # Find all connected family users
    # -------------------------------------------------
    visited = set()
    queue = deque(start_user_ids)

    all_user_ids = set(start_user_ids)

    while queue:
        current_id = queue.popleft()

        if current_id in visited:
            continue

        visited.add(current_id)

        relations = UserRelations.objects.filter(
            Q(from_user_id=current_id) |
            Q(to_user_id=current_id)
        )

        for rel in relations:
            neighbour_ids = [rel.from_user_id, rel.to_user_id]

            for uid in neighbour_ids:
                if uid not in all_user_ids:
                    all_user_ids.add(uid)
                    queue.append(uid)

    # -------------------------------------------------
    # Fetch all connected users
    # -------------------------------------------------
    users = User.objects.filter(
        id__in=all_user_ids
    ).select_related(
        "profile",
        "personal_details"
    )

    user_map = {u.id: u for u in users}

    # -------------------------------------------------
    # Relation lookup from FamilyMember
    # -------------------------------------------------
    family_members = FamilyMember.objects.filter(
        user_id__in=all_user_ids
    ).select_related("self_relation_type")

    relation_map = {}

    for fm in family_members:
        relation_map[fm.user_id] = fm.self_relation_type.name

    # -------------------------------------------------
    # Build generations
    # -------------------------------------------------
    generations = defaultdict(list)

    for user in users:
        pidhi = get_user_pidhi(user)

        node = {
            "id": user.id,
            "name": user.full_name,
            "gender": user.profile.gender,
            "pidhi": pidhi,
            "is_main_user": user.id == main_user_id
        }

        generations[str(pidhi)].append(node)

    # sort users inside pidhi
    for key in generations:
        generations[key] = sorted(
            generations[key],
            key=lambda x: x["id"]
        )

    ordered_generations = dict(
        sorted(generations.items(), key=lambda x: int(x[0]))
    )

    # -------------------------------------------------
    # Build edges (deduplicated)
    # -------------------------------------------------
    relations = UserRelations.objects.filter(
        from_user_id__in=all_user_ids,
        to_user_id__in=all_user_ids
    ).select_related("relation_type")

    edges = []
    seen = set()

    for rel in relations:
        f = rel.from_user_id
        t = rel.to_user_id
        r = rel.relation_type.name

        # spouse duplicate remove
        if r in ["husband", "wife"]:
            key = tuple(sorted([f, t])) + ("marriage",)

            if key not in seen:
                edges.append({
                    "from": f,
                    "to": t,
                    "relation": "marriage"
                })
                seen.add(key)

                # edges.append({
                #     "from": {
                #         "id": f,
                #         "name": user_map[f].full_name
                #     },
                #     "to": {
                #         "id": t,
                #         "name": user_map[t].full_name
                #     },
                #     "relation": "marriage"
                # })
                # seen.add(key)

        # sibling duplicate remove
        elif r in ["brother", "sister"]:
            key = tuple(sorted([f, t])) + ("sibling",)

            if key not in seen:
                edges.append({
                    "from": f,
                    "to": t,
                    "relation": "sibling"
                })
                seen.add(key)

                # edges.append({
                #     "from": {
                #         "id": f,
                #         "name": user_map[f].full_name
                #     },
                #     "to": {
                #         "id": t,
                #         "name": user_map[t].full_name
                #     },
                #     "relation": "sibling"
                # })
                # seen.add(key)

        # parent-child directional
        elif r in ["father", "mother"]:
            key = (f, t, r)

            if key not in seen:
                edges.append({
                    "from": f,
                    "to": t,
                    "relation": r
                })
                seen.add(key)

                # edges.append({
                #     "from": {
                #         "id": f,
                #         "name": user_map[f].full_name
                #     },
                #     "to": {
                #         "id": t,
                #         "name": user_map[t].full_name
                #     },
                #     "relation": r
                # })
                # seen.add(key)
    print("Edges:", len(edges))
    # -------------------------------------------------
    # Final Output
    # -------------------------------------------------
    return {
        "family_id": family.id,
        "family_type": family_type,
        "main_user_id": main_user_id,
        "generations": ordered_generations,
        "edges": edges
    }