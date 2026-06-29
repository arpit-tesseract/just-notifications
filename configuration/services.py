
def reassign_user_node_references(source_nodes, target_node):
    from user.models import (
        ResidentialNodeMapping, PersonalNodeMapping,
        ProfessionalPersonalNodeMapping, ProfessionalNodeMapping
    )
    source_ids = [node.id for node in source_nodes]

    res_mappings = ResidentialNodeMapping.objects.filter(node_id__in=source_ids)
    for obj in {m.residential_detail for m in res_mappings}:
        changed = False
        if obj.nodes:
            for k, v in obj.nodes.items():
                if int(v) in source_ids:
                    obj.nodes[k] = target_node.id
                    changed = True
        if changed: obj.save()
            
    per_mappings = PersonalNodeMapping.objects.filter(node_id__in=source_ids)
    for obj in {m.personal_detail for m in per_mappings}:
        changed = False
        if obj.nodes:
            for k, v in obj.nodes.items():
                if int(v) in source_ids:
                    obj.nodes[k] = target_node.id
                    changed = True
        if changed: obj.save()
            
    prof_details = {m.professional_detail for m in ProfessionalPersonalNodeMapping.objects.filter(node_id__in=source_ids)}.union(
        {m.professional_detail for m in ProfessionalNodeMapping.objects.filter(node_id__in=source_ids)})
    
    for obj in prof_details:
        changed = False
        if obj.personal_nodes:
            for k, v in obj.personal_nodes.items():
                if int(v) in source_ids:
                    obj.personal_nodes[k] = target_node.id
                    changed = True
        if obj.professional_nodes:
            for k, v in obj.professional_nodes.items():
                if int(v) in source_ids:
                    obj.professional_nodes[k] = target_node.id
                    changed = True
        if changed: obj.save()

        