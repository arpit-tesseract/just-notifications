
# def assign_module(module_name):
#     def decorator(view_func):
#         view_func.module_name = module_name
#         return view_func
#     return decorator

# utils/decorators.py
# from functools import wraps

# def assign_module(module_name):
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapped_view(*args, **kwargs):
#             return view_func(*args, **kwargs)
        
#         # attach module_name to the view function (used by DRF APIView wrapper)
#         wrapped_view.module_name = module_name
#         return wrapped_view
#     return decorator
from functools import wraps

def assign_module(module_name):
    """
    Assigns module_name to request for FBVs so permissions can read it.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Attach module_name to the request object
            print("Assigning module_name:", module_name)
            setattr(request, "module_name", module_name)
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

