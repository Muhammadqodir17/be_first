# import os
#
# from celery import shared_task
# from django.core.files import File
# from django.core.files.storage import default_storage
#
# from konkurs.models import ChildWork, Participant
# from rest_framework.response import Response
# from rest_framework import status
#
#
# @shared_task(name='celery_tasks.tasks.bulk_works_create')
# def bulk_works_create(participant_id, file_paths):
#     participant = Participant.objects.filter(id=participant_id).first()
#     if participant is None:
#         return 'Participant not found'
#
#     child_works = []
#     for path in file_paths:
#         with default_storage.open(path, 'rb') as f:
#             file_obj = File(f, name=os.path.basename(path))
#             child_works.append(
#                 ChildWork(
#                     participant=participant,
#                     competition=participant.competition,
#                     files=file_obj
#                 )
#             )
#
#     ChildWork.objects.bulk_create(child_works)
#     return 'Success'