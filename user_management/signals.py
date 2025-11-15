from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import CustomUser, ResidentialDetail


@receiver(post_delete, sender=CustomUser)
def delete_residential_details(sender, instance, **kwargs):
    print("instance:", instance)
    residential_id = instance.current_residential_details_id
    
    users_still_using_it = CustomUser.objects.filter(current_residential_details=residential_id).count()
    
    print("users_still_using_it:", users_still_using_it)
    if users_still_using_it == 0:
        try:
            print("try to delete")
            obj = ResidentialDetail.objects.get(id=residential_id)
            obj.delete()
            print("deleted")
        except:
            pass
    else:
        allocated_rooms_of_user = instance.allocated_rooms
        residential_obj = instance.current_residential_details
        print("residential_obj:", residential_obj)
        if residential_obj is not None:
            room_details = residential_obj.room_details
            pending_rooms_to_allocate = residential_obj.pending_rooms_to_allocate
            if allocated_rooms_of_user is not None:
                for room_type, total_rooms in allocated_rooms_of_user.items():
                    if room_details[room_type]["count"] != allocated_rooms_of_user[room_type]["count"]:
                        if allocated_rooms_of_user[room_type]["count"] != 1:
                            # print(True)
                            pending_rooms_to_allocate[room_type]["count"] -= 1
                        
            residential_obj.save()