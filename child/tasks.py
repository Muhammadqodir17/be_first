import os
from celery import shared_task
from django.core.files import File
from django.core.files.storage import default_storage
from konkurs.models import ChildWork, Participant

@shared_task(name='celery_tasks.tasks.bulk_works_create')
def bulk_works_create(participant_id, file_paths):
    participant = Participant.objects.get(id=participant_id)
    child_works = []

    for path in file_paths:
        with default_storage.open(path, 'rb') as f:
            file_content = File(f, name=os.path.basename(path))
            child_works.append(
                ChildWork(
                    participant=participant,
                    competition=participant.competition,
                    files=file_content
                )
            )

    ChildWork.objects.bulk_create(child_works)