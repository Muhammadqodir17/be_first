import jwt
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy  as _
from .models import BlacklistedAccessToken


class BlacklistAccessTokenMiddleware(MiddlewareMixin):
    def process_request(self, request):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            if BlacklistedAccessToken.objects.filter(token=access_token).exists():
                return JsonResponse(
                    data={'detail': _('Access token in blacklist, re-login')},
                    status=401
                )
        else:
            access_token = None


class CheckAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Exclude Rosetta and Django admin paths
        if request.path.startswith('/rosetta/') or request.path.startswith('/admin/'):
            return None

        target_urls = [
            '/api/v1/child/register_child_to_comp/',
            '/api/v1/child/add_work/',
            '/api/v1/child/create_child/',
            '/api/v1/child/update_child/',
            '/api/v1/child/get_child/',
            '/api/v1/child/get_user_children/',
            '/api/v1/child/get_children/',
            '/api/v1/child/delete_child/',
            '/api/v1/child/register_child_to_comp/',
            '/api/v1/child/get_registered_child/',
            '/api/v1/child/add_work/',
            '/api/v1/auth/get_user/',
            '/api/v1/auth/get_exist_personal_info/',
            '/api/v1/auth/personal_info/',
            '/api/v1/auth/logout/',
            '/api/v1/auth/reset_profile/',
            '/api/v1/auth/set_password/',
            '/api/v1/konkurs/get_comp_detail/',
            '/api/v1/konkurs/get_active_competitions/',
            '/api/v1/konkurs/get_finished_competitions/',
            '/api/v1/konkurs/get_grade_history/',
            '/api/v1/konkurs/get_grade_by_id/',
            '/api/v1/konkurs/get_notifications/',
            '/api/v1/konkurs/get_notification_by_id/',
            '/api/v1/konkurs/subscription/',
            '/api/v1/konkurs/unsubscription/',
        ]
        line = len(request.path)
        request_path = request.path
        index = request_path[(line - 2):-1]
        token = request.headers.get('Authorization')

        if index.isdigit() and request.path[3:-2] in target_urls:
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': _('unauthorized')}, status=401)

        if request.path[3:] in target_urls:
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': _('unauthorized')}, status=401)

        path = request.path[3:]
        if path.startswith('/api/v1/admin'):  # Changed from path[8:13] == 'admin'
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': _('unauthorized')}, status=401)
            payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('role') != 3:
                return JsonResponse(data={'error': _('Permission denied')}, status=403)

        if path.startswith('/api/v1/jury'):  # Changed from path[8:12] == 'jury'
            if token is None or len(token.split()) != 2 or token.split()[0] != 'Bearer':
                return JsonResponse(data={'error': _('unauthorized')}, status=401)
            payload = jwt.decode(token.split()[1], settings.SECRET_KEY, algorithms=['HS256'])
            # Fixed the logic error in the condition
            if payload.get('role') == 1:
                return JsonResponse(data={'error': _('Permission denied')}, status=403)