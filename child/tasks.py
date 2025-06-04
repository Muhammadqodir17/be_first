from celery import shared_task
from konkurs.models import ChildWork

@shared_task(name='celery_tasks.tasks.bulk_works_create')
def bulk_works_create(participant, files):
    child_works = [
        ChildWork(
            participant=participant,
            competition=participant.competition,
            files=file
        )
        for file in files
    ]
    ChildWork.objects.bulk_create(child_works)