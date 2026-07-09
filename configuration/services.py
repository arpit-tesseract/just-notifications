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

def count_user_node_references(node_id):
    from user.models import (
        ResidentialNodeMapping, PersonalNodeMapping,
        ProfessionalPersonalNodeMapping, ProfessionalNodeMapping
    )
    count = 0
    count += ResidentialNodeMapping.objects.filter(node_id=node_id).count()
    count += PersonalNodeMapping.objects.filter(node_id=node_id).count()
    count += ProfessionalPersonalNodeMapping.objects.filter(node_id=node_id).count()
    count += ProfessionalNodeMapping.objects.filter(node_id=node_id).count()
    return count