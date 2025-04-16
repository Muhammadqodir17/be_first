import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class CheckAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        target_urls = [
            '/api/v1/child/register_child_to_comp/',
            '/api/v1/child/add_work/',
            '/api/v1/child/create_child/',
            '/api/v1/child/update_child/',
            '/api/v1/child/get_child/',
            '/api/v1/child/get_user_children/',
            '/api/v1/child/get_children/',
            '/api/v1/child/delete_child/',
            '/api/v1/auth/user/',
            '/api/v1/auth/set_profile/',
            '/api/v1/konkurs/get_comp_detail/',
            '/api/v1/konkurs/get_active_competitions/',
            '/api/v1/konkurs/get_finished_competitions/',
            '/api/v1/konkurs/get_grade_history/',
            '/api/v1/konkurs/get_grade_by_id/',
            '/api/v1/konkurs/get_notifications/',
            '/api/v1/konkurs/get_notification_by_id/',
        ]
        line = len(request.path)
        request_path = request.path
        index = request_path[(line - 2):-1]
        token = request.headers.get('Authorization')

        if index.isdigit() and request.path[:-2] in target_urls:
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': 'unauthorized'}, status=401)

        if request.path in target_urls:
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': 'unauthorized'}, status=401)

        path = request.path
        if path[8:13] == 'admin':
            payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('role') != 3:
                return JsonResponse(data={'error': 'Permission denied'}, status=403)

        if path[8:12] == 'jury':
            payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('role') != 2 or payload.get('role') != 3:
                return JsonResponse(data={'error': 'Permission denied'}, status=403)

# class RolePermissionMiddleware(MiddlewareMixin):
#     def process_request(self, request):
#         path = request.path
#         if path[8:13] == 'admin':
#             token = request.headers.get('Authorization')
#             if not token:
#                 return JsonResponse(data={'error': 'Not authenticated'}, status=401)
#             if token.split()[0] != 'Bearer':
#                 return JsonResponse(data={'error': 'Bearer is missed'}, status=400)
#             payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
#             if payload.get('role') != 3:
#                 return JsonResponse(data={'error': 'Permission denied'}, status=403)
#
#         if path[8:12] == 'jury':
#             token = request.headers.get('Authorization')
#             if not token:
#                 return JsonResponse(data={'error': 'Not authenticated'}, status=401)
#             if token.split()[0] != 'Bearer':
#                 return JsonResponse(data={'error': 'Bearer is missed'}, status=400)
#             payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
#             if payload.get('role') != 2 or payload.get('role') != 3:
#                 return JsonResponse(data={'error': 'Permission denied'}, status=403)