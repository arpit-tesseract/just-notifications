from django.db.models import Count, Q
from configuration.models import Dimension, Level, Node
from .models import User, UserPersonalDetails, RelationType, UserRelations, Family, FamilyMember, ResidentialDetails, ResidentialNodeMapping, UserRole, _generate_code_from_nodes

def get_all_role_descendant_names(role_name, include_self=True):
    descendant_names = set()
    if include_self:
        descendant_names.add(role_name)
    
    roles_to_check = list(UserRole.objects.filter(parent__name=role_name, is_active=True).values_list('name', flat=True))
    
    while roles_to_check:
        current_name = roles_to_check.pop(0)
        descendant_names.add(current_name)
        children = list(UserRole.objects.filter(parent__name=current_name, is_active=True).values_list('name', flat=True))
        roles_to_check.extend(children)
        
    return list(descendant_names)

def get_residential_details_ids_by_code(residential_code):
    """
    Return a list of ResidentialDetails PKs whose computed residential_code
    matches the given string.

    residential_code is a Python @property (not a DB column), so we cannot
    use it in an ORM filter. Instead, we fetch all ResidentialDetails that
    have at least one node mapping and compute the code in Python.
    """
    if not residential_code:
        return []

    # Collect all residential_detail IDs that have mappings
    residential_ids_with_mappings = (
        ResidentialNodeMapping.objects
        .values_list('residential_detail_id', flat=True)
        .distinct()
    )

    matching_ids = []
    for rd_id in residential_ids_with_mappings:
        mappings_qs = ResidentialNodeMapping.objects.filter(
            residential_detail_id=rd_id
        )
        code = _generate_code_from_nodes(mappings_qs)
        if code == residential_code:
            matching_ids.append(rd_id)

    return matching_ids


def get_or_create_residential_details(nodes_json):
    if not nodes_json or not isinstance(nodes_json, dict):
        return ResidentialDetails.objects.create(), True

    target_node_ids = [int(nid) for nid in nodes_json.values() if nid]
    target_length = len(target_node_ids)

    existing_residential = ResidentialDetails.objects.annotate(
        total_mappings=Count('node_mappings'),
        matched_mappings=Count('node_mappings', filter=Q(node_mappings__node_id__in=target_node_ids))
    ).filter(
        total_mappings=target_length,
        matched_mappings=target_length
    ).first()

    if existing_residential:
        return existing_residential, False

    residential_obj = ResidentialDetails.objects.create()
    mappings_to_create = []
    for level_id, node_id in nodes_json.items():
        if level_id and node_id:
            mappings_to_create.append(
                ResidentialNodeMapping(
                    residential_detail=residential_obj, level_id=int(level_id), node_id=int(node_id)
                )
            )
    if mappings_to_create:
        ResidentialNodeMapping.objects.bulk_create(mappings_to_create)
    return residential_obj, True


def get_level_node_mapping(mapping_qs):
    if not mapping_qs:
        return {}
    
    node_dict = {}
    for mapping in mapping_qs.select_related('node'):
        node_dict[str(mapping.level_id)] = {
            "id": mapping.node.id,
            "name": mapping.node.name
        }
    return node_dict


def get_pidhi_node_from_personal_details(personal_details_obj):
    if not personal_details_obj:
        return None
    
    try:
        dimension_obj = Dimension.objects.get(name="Personal")
        pidhi_level_obj = Level.objects.get(name="pidhi", dimension=dimension_obj)
    except (Dimension.DoesNotExist, Level.DoesNotExist):
        return None

    mapping = personal_details_obj.node_mappings.filter(level=pidhi_level_obj).select_related('node').first()
    if mapping:
        return mapping.node
    return None



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
        return None

    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else None


# ---------------------------------------------------------
# Helper: Get pidhi from user.personal_details
# ---------------------------------------------------------
def get_user_pidhi(user):
    personal = getattr(user, "personal_details", None)

    pidhi_node = get_pidhi_node_from_personal_details(personal)

    if not pidhi_node:
        return None

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

    members = family.members.exclude(
    self_relation_type__name__in=["worker", "guest"]
)
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
            Q(to_user_id=current_id),
            relation_type__category="general"
        ).select_related("relation_type")

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

        if pidhi:
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
        to_user_id__in=all_user_ids,
        relation_type__category="general"
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
    # Hide unconnected users (Worker, Guest, etc.)
    # -------------------------------------------------
    connected_ids = set()

    for edge in edges:
        connected_ids.add(edge["from"])
        connected_ids.add(edge["to"])

    filtered_generations = {}

    for pidhi, members in ordered_generations.items():
        filtered = [
            member for member in members
            if member["id"] in connected_ids
        ]

        if filtered:
            filtered_generations[pidhi] = filtered


    # -------------------------------------------------
    # Final Output
    # -------------------------------------------------
    return {
        "family_id": family.id,
        "family_type": family_type,
        "main_user_id": main_user_id,
        "generations": filtered_generations,
        "edges": edges
    }

# =============================================================================
# CROSS-LINKED FAMILY TREE
# All helpers below support build_complete_family_tree().
# build_family_tree_by_pidhi() above is completely unchanged.
#
# Design principles:
#   - ONE level of linked_trees per response (frontend navigates by re-calling the API).
#   - No recursion. No hard-coded relation maps.
#   - Cross-family boundary detected from the graph itself (users outside all_user_ids).
#   - Two bulk ORM queries total for the discovery pass.
#   - visited_family_ids prevents duplicate processing within a single request.
# =============================================================================


# ---------------------------------------------------------------------------
# Helper 1 – find_family_for_user
# STATUS: UNCHANGED
# ---------------------------------------------------------------------------
def find_family_for_user(user_id: int) -> "Family | None":
    """
    Return the Family whose FamilyMember record points at *user_id*.
    Prefers the family where the user is the main user (husband).
    Returns None when the user has no family membership.
    Single ORM query with select_related.
    """
    member = (
        FamilyMember.objects
        .filter(user_id=user_id)
        .select_related("family")
        .order_by("-is_main_user")   # True (1) sorts before False (0)
        .first()
    )
    return member.family if member else None


# ---------------------------------------------------------------------------
# Helper 2 – get_relation_label_to_main_user
# STATUS: MODIFIED  (was get_relationship_to_main_user)
#
# Changes:
#   - Removed _GATEWAY_RELATION_LABEL_MAP lookup entirely.
#   - Returns relation_type.name directly from the graph — no hard-coding.
#   - Accepts pre-fetched relation rows to avoid any per-call ORM query
#     when called from collect_cross_family_connections.
# ---------------------------------------------------------------------------
def get_relation_label_to_main_user(
    main_user_id: int,
    gateway_user_id: int,
    preloaded_relations: "dict | None" = None,
) -> str:
    """
    Return how *gateway_user_id* is related to *main_user_id*.

    Label = relation_type.name as stored in UserRelations.
    Examples: "wife", "son", "daughter", "father", "mother".

    *preloaded_relations* — optional dict of shape
        {(from_uid, to_uid): relation_type_name}
    built once by the caller to eliminate per-row ORM queries.

    Falls back to a single DB query only when preloaded_relations is None
    or when the pair is not found in it.
    """
    if preloaded_relations is not None:
        # Check both directions in the preloaded map.
        label = preloaded_relations.get((main_user_id, gateway_user_id))
        if label:
            return label
        label = preloaded_relations.get((gateway_user_id, main_user_id))
        if label:
            return label

    # Fallback: direct DB lookup (used only when called without preloaded data).
    rel = (
        UserRelations.objects
        .filter(
            from_user_id=main_user_id,
            to_user_id=gateway_user_id,
        )
        .select_related("relation_type")
        .first()
    )
    if rel:
        return rel.relation_type.name

    rel = (
        UserRelations.objects
        .filter(
            from_user_id=gateway_user_id,
            to_user_id=main_user_id,
        )
        .select_related("relation_type")
        .first()
    )
    if rel:
        return rel.relation_type.name

    return "related"


# ---------------------------------------------------------------------------
# Helper 3 – collect_cross_family_connections
# STATUS: MODIFIED
#
# Changes:
#   - Discovery criterion changed: any UserRelation where to_user is
#     OUTSIDE all_user_ids — i.e., the graph boundary itself.
#     No longer depends on relation_type__category as the primary filter.
#   - Eliminated N+1: relation label resolved from pre-loaded dict of
#     main_user's own relations (one extra bulk query), not per-row calls.
#   - Deduplication key is now family_id alone (one entry per linked family).
# ---------------------------------------------------------------------------
def collect_cross_family_connections(
    main_user_id: int,
    all_user_ids: set,
    visited_family_ids: set,
) -> list:
    """
    Find every UserRelations edge that crosses the boundary of the current
    family graph, i.e. from_user IN all_user_ids AND to_user NOT IN all_user_ids.

    These boundary edges point at users who may belong to other registered
    families.

    Returns a deduplicated list (one entry per distinct linked family):
        [
            {
                "family":       <Family instance>,
                "through_user": <int — the family member who has the link>,
                "relationship": <str — relation_type.name from UserRelations>,
            },
            ...
        ]

    Total ORM queries: 3
        1. UserRelations boundary edges.
        2. FamilyMember bulk lookup for all discovered external users.
        3. UserRelations between main_user and all current family members
           (for label resolution — one query, result cached in a dict).
    """
    if not all_user_ids:
        return []

    # ------------------------------------------------------------------
    # Query 1: all boundary edges — from inside the family, to outside.
    # Exclude edges where the to_user is also in the current family graph
    # to avoid treating internal "general" relations as cross-links.
    # ------------------------------------------------------------------
    boundary_edges = list(
        UserRelations.objects
        .filter(from_user_id__in=all_user_ids)
        .exclude(to_user_id__in=all_user_ids)
        .select_related("relation_type")
        .values_list(
            "from_user_id",
            "to_user_id",
            "relation_type__name",
            "relation_type__category",
        )
    )

    if not boundary_edges:
        return []

    external_user_ids: set = {row[1] for row in boundary_edges}

    # ------------------------------------------------------------------
    # Query 2: FamilyMember rows for all external users in one shot.
    # Order by -is_main_user so the main-user membership wins when a
    # person belongs to multiple families.
    # ------------------------------------------------------------------
    memberships = (
        FamilyMember.objects
        .filter(user_id__in=external_user_ids)
        .select_related("family")
        .order_by("-is_main_user")
    )
    # user_id → Family (first hit wins because of the ordering above)
    user_family_map: dict = {}
    for m in memberships:
        if m.user_id not in user_family_map:
            user_family_map[m.user_id] = m.family

    # ------------------------------------------------------------------
    # Query 3: preload all UserRelations between main_user and every
    # member currently inside the family graph — used for label resolution
    # without any per-row query.
    # ------------------------------------------------------------------
    main_user_relations = list(
        UserRelations.objects
        .filter(
            Q(from_user_id=main_user_id, to_user_id__in=all_user_ids) |
            Q(from_user_id__in=all_user_ids, to_user_id=main_user_id),
        )
        .select_related("relation_type")
        .values_list("from_user_id", "to_user_id", "relation_type__name")
    )
    # Build lookup: (from_uid, to_uid) → relation_name
    relation_lookup: dict = {(f, t): name for f, t, name in main_user_relations}

    # ------------------------------------------------------------------
    # Build result list — deduplicate by family_id only.
    # One entry per linked family regardless of how many boundary edges
    # point into it.
    # ------------------------------------------------------------------
    seen_family_ids: set = set()
    results: list = []

    for from_uid, to_uid, rel_name, rel_category in boundary_edges:
        linked_family = user_family_map.get(to_uid)

        if linked_family is None:
            # External user has no registered family yet — skip silently.
            continue

        if linked_family.id in visited_family_ids:
            # Already processed or is the root family — skip.
            continue

        if linked_family.id in seen_family_ids:
            # Already emitting this family from a different edge — skip.
            continue

        seen_family_ids.add(linked_family.id)

        # Resolve how the gateway member (from_uid) relates to main_user.
        # Uses preloaded dict — zero extra DB queries.
        relationship_label = get_relation_label_to_main_user(
            main_user_id=main_user_id,
            gateway_user_id=from_uid,
            preloaded_relations=relation_lookup,
        )

        results.append({
            "family":       linked_family,
            "through_user": from_uid,
            "relationship": relationship_label,
        })

    return results


# ---------------------------------------------------------------------------
# Helper 4 – _build_single_linked_tree_entry
# STATUS: NEW  (replaces the recursive build_linked_tree)
#
# Flat. Non-recursive. Builds one family's tree data and wraps it in the
# linked_trees entry format. The nested linked_trees key is always [].
# Frontend navigates deeper by calling the API again with this family's
# main_user_id.
# ---------------------------------------------------------------------------
def _build_single_linked_tree_entry(
    family_id: int,
    relationship_label: str,
    through_user_id: int,
) -> dict:
    """
    Build the family tree for *family_id* (using the unchanged
    build_family_tree_by_pidhi) and wrap it in the linked_trees entry format.

    linked_trees inside this entry is always [] — the frontend must call
    the API again to navigate further.

    Returns {} if the family does not exist.
    """
    try:
        tree = build_family_tree_by_pidhi(family_id)
    except Family.DoesNotExist:
        return {}
    except Exception:
        return {}

    # Flat: this linked family's own linked_trees is empty.
    # The caller (the frontend) navigates further by re-calling the API.
    tree["linked_trees"] = []

    return {
        "relationship_to_main_user": relationship_label,
        "through_user":              through_user_id,
        "family":                    tree,
    }


# ---------------------------------------------------------------------------
# Helper 5 – discover_linked_families
# STATUS: MODIFIED
#
# Changes:
#   - Removed recursive build_linked_tree call.
#   - Now calls flat _build_single_linked_tree_entry.
#   - visited_family_ids still prevents duplicate family processing
#     within the same request (e.g. two boundary edges into the same family).
# ---------------------------------------------------------------------------
def discover_linked_families(
    main_user_id: int,
    root_family_id: int,
    all_user_ids: set,
) -> list:
    """
    Discover all directly linked families for the current family tree and
    return a list of linked_trees entries (one level deep only).

    *root_family_id* is pre-added to visited_family_ids so the root family
    is never emitted as a linked tree of itself.
    """
    # Fresh per-request visited set — root family is pre-marked.
    visited_family_ids: set = {root_family_id}

    connections = collect_cross_family_connections(
        main_user_id=main_user_id,
        all_user_ids=all_user_ids,
        visited_family_ids=visited_family_ids,
    )

    linked_trees: list = []
    for conn in connections:
        # Mark as visited so if two connections point at the same family
        # the second one is dropped by collect_cross_family_connections on
        # the next call (already handled by seen_family_ids there, but we
        # also update visited_family_ids for safety).
        visited_family_ids.add(conn["family"].id)

        entry = _build_single_linked_tree_entry(
            family_id=conn["family"].id,
            relationship_label=conn["relationship"],
            through_user_id=conn["through_user"],
        )
        if entry:
            linked_trees.append(entry)

    return linked_trees


# ---------------------------------------------------------------------------
# PUBLIC ENTRY POINT – build_complete_family_tree
# STATUS: UNCHANGED
# ---------------------------------------------------------------------------
def build_complete_family_tree(family_id: int) -> dict:
    """
    Drop-in replacement for build_family_tree_by_pidhi() called from views.

    Calls the existing function (completely unchanged), then appends the
    linked_trees key.  The response is a strict superset of the original:

        {
            "family_id":    int,
            "family_type":  str | None,
            "main_user_id": int | None,
            "generations":  dict,
            "edges":        list,
            "linked_trees": list          ← added
        }

    linked_trees contains only DIRECTLY linked families (one level).
    The frontend navigates deeper by calling the same API with a linked
    family's main_user_id.
    """
    # --- EXISTING CODE (UNCHANGED) -----------------------------------------
    data = build_family_tree_by_pidhi(family_id)
    # -----------------------------------------------------------------------

    main_user_id = data.get("main_user_id")
    if main_user_id is None:
        data["linked_trees"] = []
        return data

    # Collect all user IDs the existing function already resolved.
    all_user_ids: set = set()
    for gen_users in data.get("generations", {}).values():
        for person in gen_users:
            all_user_ids.add(person["id"])

    data["linked_trees"] = discover_linked_families(
        main_user_id=main_user_id,
        root_family_id=family_id,
        all_user_ids=all_user_ids,
    )

    return data


# =============================================================================
# END OF CROSS-LINKED FAMILY TREE CODE
# =============================================================================

from rest_framework.exceptions import ValidationError

def validate_dimension_nodes(value, dimension_obj):
    # 1. Allow null/empty values to pass through if they aren't required
    if not value:
        return value
        
    # 2. Ensure it is actually a dictionary {...}, not a list [...]
    if not isinstance(value, dict):
        raise ValidationError("Must be a JSON object.")
    
    valid_level_ids = set(Level.objects.filter(dimension=dimension_obj).values_list('id', flat=True))
    valid_node_ids = set(Node.objects.filter(dimension=dimension_obj).values_list('id', flat=True))

    # 3. Validate that every Key (Level) and Value (Node) is a valid ID
    for level_id, node_id in value.items():
        if not str(level_id).isdigit():
            raise ValidationError(f"Invalid Level ID '{level_id}'. It must be numeric.")
        
        if not str(node_id).isdigit(): 
            raise ValidationError({
                level_id: f"Invalid Node ID '{node_id}'. It must be numeric."
            })
        
        if int(level_id) not in valid_level_ids:
            raise ValidationError({
                level_id: f"Invalid Level ID '{level_id}' for dimension '{dimension_obj.name}'."
            })

        if int(node_id) not in valid_node_ids:
            raise ValidationError({
                level_id: f"Invalid Node ID '{node_id}' for dimension '{dimension_obj.name}'."
            })

    # 4. Enforce Mandatory Levels (GAP-05)
    mandatory_levels = Level.objects.filter(
        dimension=dimension_obj, 
        is_mandatory=True, 
        is_deleted=False
    )
    
    missing_mandatory = []
    for level in mandatory_levels:
        if str(level.id) not in value:
            missing_mandatory.append(level.name)
            
    if missing_mandatory:
        missing_names = ", ".join(missing_mandatory)
        raise ValidationError(
            f"Missing required node(s) for the following level(s): {missing_names}"
        )

    return value