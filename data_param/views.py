from respond.models import DataFile
from django.db.models import QuerySet
from data_param.models import FileControl
from inai.models import Petition


def get_related_file_controls(
        data_file: DataFile = None, petition: Petition = None) \
        -> QuerySet[FileControl]:

    if petition is None:
        if data_file is None:
            raise ValueError("Either data_file or petition must be provided")
        petition = data_file.petition_file_control.petition

    has_real_provider = getattr(petition, "real_provider", None)

    base_controls = FileControl.objects \
        .filter(file_format__isnull=False) \
        .exclude(data_group_id="orphan")

    if has_real_provider:
        provider = petition.real_provider
        provider_controls = base_controls \
            .filter(petition_file_control__petition__real_provider=provider)\
            .distinct()
    else:
        provider = petition.agency.provider
        provider_controls = base_controls \
            .filter(petition_file_control__petition__agency__provider=provider)\
            .distinct()
    near_file_controls = provider_controls \
        .filter(petition_file_control__petition=petition) \
        .prefetch_related("file_format", "columns")
    others_file_controls = provider_controls \
        .exclude(petition_file_control__petition=petition) \
        .prefetch_related("file_format", "columns")
    return near_file_controls | others_file_controls
