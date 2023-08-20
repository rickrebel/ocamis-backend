import boto3
from django.conf import settings


def obtain_names_from_s3(
        path, folio_petition, is_reply_file=False, file_control_id=None):
    from inai.models import (
        DataFile, PetitionFileControl, Petition, ReplyFile, FileType)
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    s3 = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    my_bucket = s3.Bucket(bucket_name)
    for object_summary in my_bucket.objects.filter(Prefix=path):
        # Delimiter = '/', MaxKeys = 1000, StartAfter = f"{path}{folio_petition}"):
        print(object_summary.key)
        final_name = object_summary.key.replace(f"{settings.AWS_LOCATION}/", '')
        if is_reply_file:
            try:
                default_type = FileType.objects.get(name="no_final_info")
                petition = Petition.objects.get(folio_petition=folio_petition)
                pf, created = ReplyFile.objects.get_or_create(
                    petition=petition,
                    file=final_name,
                    file_type=default_type,
                    has_data=True
                    )
                print(f"{'Exitosamente' if created else 'Previamente'} creado: {petition}")
            except Exception as e:
                print("No fue posible obtener la Solicitud")
                print(e)
        else:
            try:
                pet_file_ctrls = PetitionFileControl.objects.filter(
                    petition__folio_petition=folio_petition)
                if file_control_id:
                    pet_file_ctrls = pet_file_ctrls.filter(
                        file_control_id=file_control_id)
                pet_file_ctrl = pet_file_ctrls.first()
                petition = pet_file_ctrl.petition
                entity = petition.real_entity or petition.agency.entity
                DataFile.objects.create(
                    petition_file_control=pet_file_ctrl,
                    entity=entity,
                    file=final_name)
                print(f"Exitosamente creado {pet_file_ctrl}")
            except Exception as e:
                print("No fue posible obtener el pet_file_ctrl")
                print(e)
        print("------------------------------")


# obtain_names_from_s3("data_files/nacional/issste/202107/", "0063700513521", True)
# obtain_names_from_s3("data_files/nacional/imss/202112/", "330018022027342", True)
# obtain_names_from_s3("data_files/nacional/imss/202107/", "0064102300821", True)
# obtain_names_from_s3("data_files/nacional/issste/202201/reporte_recetas_", "330017122000929", True)
# obtain_names_from_s3(
#     "data_files/nacional/issste/0063700513521/recetas_2018", "0063700513521",
#     False, 1165)
# obtain_names_from_s3(
#     "data_files/nacional/issste/330017123002614/drive-download-", "330017123002614",
#     True)


def delete_paths_from_aws(path):
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    s3 = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    my_bucket = s3.Bucket(bucket_name)
    count = 0
    for object_summary in my_bucket.objects.filter(Prefix=path):
        count += 1
        # object_summary.delete()
    print("count", count)


# delete_paths_from_aws("data_files/req_noviembre_2018_02_")
