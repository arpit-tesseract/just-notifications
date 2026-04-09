from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Node, NodeClosure

# 1. PRE-SAVE: Capture the old parent so we know if it changed
@receiver(pre_save, sender=Node)
def capture_old_parent(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Node.objects.get(pk=instance.pk)
            instance._old_parent_id = old_instance.parent_id
        except Node.DoesNotExist:
            instance._old_parent_id = None
    else:
        instance._old_parent_id = None

# 2. POST-SAVE: Handle Creation AND Updates
@receiver(post_save, sender=Node)
def manage_node_closure(sender, instance, created, **kwargs):
    # A. HANDLE NEW NODE CREATION (Your existing logic)
    if created:
        # 1. Create Self-Reference
        NodeClosure.objects.create(
            dimension=instance.dimension,
            ancestor=instance,
            descendant=instance,
            depth=0
        )
        # 2. Copy paths from Parent
        if instance.parent:
            parents_closures = NodeClosure.objects.filter(
                dimension=instance.dimension,
                descendant=instance.parent
            )
            new_closures = []
            for closure in parents_closures:
                new_closures.append(NodeClosure(
                    dimension=instance.dimension,
                    ancestor=closure.ancestor,
                    descendant=instance,
                    depth=closure.depth + 1
                ))
            NodeClosure.objects.bulk_create(new_closures)

    # B. HANDLE RE-PARENTING (Update)
    else:
        old_parent_id = getattr(instance, '_old_parent_id', None)
        new_parent_id = instance.parent_id

        # Only run if the parent actually changed
        if old_parent_id != new_parent_id:
            with transaction.atomic():
                # 1. Identify the Subtree
                # Get all descendants of the moving node (including itself)
                subtree_ids = NodeClosure.objects.filter(
                    dimension=instance.dimension,
                    ancestor=instance
                ).values_list('descendant_id', flat=True)

                # 2. DISCONNECT from Old Ancestors
                # Delete paths where:
                # - The Descendant is in our moving subtree
                # - BUT The Ancestor is NOT in our moving subtree (meaning it's an old parent/grandparent)
                NodeClosure.objects.filter(
                    dimension=instance.dimension,
                    descendant_id__in=subtree_ids
                ).exclude(
                    ancestor_id__in=subtree_ids
                ).delete()


                # 3. RECONNECT to New Ancestors (if valid parent exists)
                if instance.parent:
                    # Get all paths ending at the NEW parent (The new superstructure)
                    new_ancestor_paths = NodeClosure.objects.filter(
                        dimension=instance.dimension,
                        descendant=instance.parent
                    )
                    
                    # Get all paths starting at ME (The moving subtree structure)
                    # We need to preserve the relative structure of children below India
                    subtree_paths = NodeClosure.objects.filter(
                        dimension=instance.dimension,
                        ancestor=instance
                    )

                    new_closures = []
                    
                    # Cross-Join: Connect every New Ancestor -> Every Subtree Node
                    for super_path in new_ancestor_paths:
                        for sub_path in subtree_paths:
                            new_closures.append(NodeClosure(
                                dimension=instance.dimension,
                                ancestor_id=super_path.ancestor_id,   # e.g., Earth
                                descendant_id=sub_path.descendant_id, # e.g., India (or Mumbai)
                                depth=super_path.depth + 1 + sub_path.depth
                            ))
                    
                    NodeClosure.objects.bulk_create(new_closures)