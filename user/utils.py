from configuration.models import Dimension, Level, Node

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


