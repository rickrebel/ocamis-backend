from django.core.management.base import BaseCommand

from intl_medicine.models import PrioritizedComponent


class Command(BaseCommand):
    help = 'Calcula cuando las respuestas fueron cambiadas'

    def handle(self, *args, **options):
        base_responses = PrioritizedComponent.objects.filter(
            group_answer__respondent__isnull=True)
        responses = PrioritizedComponent.objects.filter(
            group_answer__respondent__isnull=False,
            group_answer__is_valid=True)

        for base_response in base_responses:
            current_responses = responses\
                .filter(component=base_response.component)\
                .exclude(is_prioritized=base_response.is_prioritized)
            current_responses.update(was_changed=True)
