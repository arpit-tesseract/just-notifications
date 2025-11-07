from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import CustomUser, ResidentialDetail


@receiver(post_delete, sender=CustomUser)
def delete_residential_details(sender, instance, **kwargs):
    print("instance:", instance)
    residential_id = instance.residential_details_id
    
    users_still_using_it = CustomUser.objects.filter(residential_details=residential_id).count()
    
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
        residential_obj = instance.residential_details
        room_details = residential_obj.room_details
        pending_rooms_to_allocate = residential_obj.pending_rooms_to_allocate
        if allocated_rooms_of_user is not None:
            for room_type, total_rooms in allocated_rooms_of_user.items():
                # print("room_type:", room_type)
                # print("room_details[room_type]:", room_details[room_type])
                # print("allocated_rooms_of_user[room_type]:", allocated_rooms_of_user[room_type])
                # print("pending_rooms_to_allocate[room_type]:", pending_rooms_to_allocate[room_type])
                if room_details[room_type] != allocated_rooms_of_user[room_type]:
                    if allocated_rooms_of_user[room_type] != 1:
                        # print(True)
                        pending_rooms_to_allocate[room_type] -= 1
                        
        residential_obj.save()