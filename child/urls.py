from django.urls import path
from .views import (
    ChildViewSet,
    RegisterChildToCompViewSet,
    ChildWorkViewSet
)

urlpatterns = [
    # add child
    path('create_child/', ChildViewSet.as_view({'post': 'create'}), name='create_child'),
    path('update_child/<int:pk>/', ChildViewSet.as_view({'put': 'update', 'patch': 'update'}),
         name='update_child_by_id'),
    path('get_child/<int:pk>/', ChildViewSet.as_view({'get': 'get_by_id'}), name='get_child_by_id'),
    path('get_user_children/', ChildViewSet.as_view({'get': 'get_user_children'}), name='get_user_children'),
    path('get_children/', ChildViewSet.as_view({'get': 'list'}), name='get_list_of_child'),
    path('delete_child/<int:pk>/', ChildViewSet.as_view({'delete': 'delete'}), name='delete_child_by_id'),
    # register
    path('register_child_to_comp/', RegisterChildToCompViewSet.as_view({'post': 'create'}),
         name='register_child_to_comp'),
    # add work
    path('add_work/', ChildWorkViewSet.as_view({'post': 'create'}), name='add_work'),
]
