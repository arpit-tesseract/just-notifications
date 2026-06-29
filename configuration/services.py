def reassign_user_node_references(source_nodes, target_node):
    from user.models import (
        ResidentialNodeMapping, PersonalNodeMapping,
        ProfessionalPersonalNodeMapping, ProfessionalNodeMapping
    )
    source_ids = [node.id for node in source_nodes]

    ResidentialNodeMapping.objects.filter(node_id__in=source_ids).update(node=target_node)
    PersonalNodeMapping.objects.filter(node_id__in=source_ids).update(node=target_node)
    ProfessionalPersonalNodeMapping.objects.filter(node_id__in=source_ids).update(node=target_node)
    ProfessionalNodeMapping.objects.filter(node_id__in=source_ids).update(node=target_node)