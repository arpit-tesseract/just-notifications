# configuration/signals.py

from django.db.models.signals import post_save, post_delete
from .models import Node, NodeClosure, Level
from django.dispatch import receiver
from django.db.models import F
from django.db import transaction

@receiver(post_save, sender=Node)
def create_node_closure(sender, instance, created, **kwargs):
    """
    Automatically populates the NodeClosure table when a new Node is created.
    """
    if created:
        # 1. Create Self-Reference (Depth 0)
        NodeClosure.objects.create(
            dimension=instance.dimension,
            ancestor=instance,
            descendant=instance,
            depth=0
        )
        
        # 2. Copy all paths from the Parent
        if instance.parent:
            parents_closures = NodeClosure.objects.filter(descendant=instance.parent)
            
            new_closures = []
            for closure in parents_closures:
                new_closures.append(NodeClosure(
                    dimension=instance.dimension,
                    ancestor=closure.ancestor, 
                    descendant=instance,       
                    depth=closure.depth + 1
                ))
            
            NodeClosure.objects.bulk_create(new_closures)


@receiver(post_delete, sender=Level)
def reorder_levels_on_delete(sender, instance, **kwargs):
    """
    When a Level is deleted, shift all subsequent levels UP by 1.
    Example: If Level 3 is deleted, Level 4 becomes 3, Level 5 becomes 4.
    """
    if instance.sort_order is not None:
        with transaction.atomic():
            Level.objects.filter(
                dimension=instance.dimension,
                sort_order__gt=instance.sort_order
            ).update(sort_order=F('sort_order') - 1)