import boto3
from django.conf import settings

#obtain_names_from_s3("data_files/nacional/imss/202107/", "0064102300821")
def obtain_names_from_s3(path, folio_petition, is_process_file=False):
    from inai.models import (
        DataFile, PetitionFileControl, Petition, ProcessFile, FileType)
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    s3 = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    my_bucket = s3.Bucket(bucket_name)
    for object_summary in my_bucket.objects.filter(Prefix=path):
        print(object_summary.key)
        final_name = object_summary.key.replace(f"{settings.AWS_LOCATION}/", '')
        if not is_process_file:
            try:
                pet_file_ctrl = PetitionFileControl.objects.get(
                    petition__folio_petition=folio_petition)
                DataFile.objects.create(
                    petition_file_control=pet_file_ctrl,
                    file=final_name)
                print(f"Exitosamente creado {pet_file_ctrl}")
            except Exception as e:
                print("No fue posible obtener el pet_file_ctrl")
                print(e)
        else:
            try:
                default_type = FileType.objects.get(name="no_final_info")
                petition = Petition.objects.get(folio_petition=folio_petition)
                ProcessFile.objects.create(
                    petition=petition,
                    file=final_name,
                    file_type=default_type,
                    )
                print(f"Exitosamente creado {petition}")
            except Exception as e:
                print("No fue posible obtener la Solicitud")
                print(e)
        print("------------------------------")




#obtain_names_from_s3("data_files/nacional/issste/202107/", "0063700513521", True)
obtain_names_from_s3("data_files/nacional/imss/202112/", "330018022027342", True)
#obtain_names_from_s3("data_files/nacional/imss/202107/", "0064102300821", True)


