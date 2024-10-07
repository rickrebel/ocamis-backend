import boto3
from django.conf import settings


def obtain_names_from_s3(
        path, folio_petition, is_reply_file=False, file_control_id=None):
    from inai.models import PetitionFileControl, Petition
    from respond.models import DataFile, ReplyFile
    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    s3 = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    my_bucket = s3.Bucket(bucket_name)
    all_files = my_bucket.objects.filter(Prefix=path)
    print("all_files", all_files)
    for object_summary in all_files:
        # Delimiter = '/', MaxKeys = 1000, StartAfter = f"{path}{folio_petition}"):
        print(object_summary.key)
        final_name = object_summary.key.replace(f"{settings.AWS_LOCATION}/", '')
        if is_reply_file:
            try:
                petition = Petition.objects.get(folio_petition=folio_petition)
                pf, created = ReplyFile.objects.get_or_create(
                    petition=petition, file=final_name, has_data=True)
                print(f"{'Exitosamente' if created else 'Previamente'} creado: {petition}")
            except Exception as e:
                print("No fue posible obtener la Solicitud")
                print(e)
        else:
            try:
                if file_control_id:
                    pet_file_ctrls = PetitionFileControl.objects.filter(
                        file_control_id=file_control_id)
                else:
                    pet_file_ctrls = PetitionFileControl.objects.filter(
                        petition__folio_petition=folio_petition)
                pet_file_ctrl = pet_file_ctrls.first()
                petition = pet_file_ctrl.petition
                provider = petition.real_provider or petition.agency.provider
                DataFile.objects.get_or_create(
                    petition_file_control=pet_file_ctrl,
                    provider=provider, file=final_name)
                print(f"Exitosamente creado {pet_file_ctrl}")
            except Exception as e:
                print("No fue posible obtener el pet_file_ctrl")
                print(e)
        print("------------------------------")


# obtain_names_from_s3(
#     "data_files/estatal/sspue/211200722000896/",
#     "211200722000896", True)

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


def apply_transformation_to_file():
    obtain_names_from_s3(
        "data_files/nacional/imss_imss-bienestar/330018024006508/dvd3/",
        "330018024006508", True)


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


def upload_s3_files(local_file, s3_dir):
    from django.utils import timezone
    # import boto3.s3.transfer as s3transfer
    from scripts.common import build_s3, start_session
    s3 = build_s3()
    # print("s3: ", s3)
    print("start time: ", timezone.now())

    s3_client, _ = start_session(endpoint_url="True")
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=s3["aws_access_key_id"],
    #     aws_secret_access_key=s3["aws_secret_access_key"],
    # )
    bucket_name = s3["bucket_name"]
    # bucket_name = "cdn-desabasto.s3-accelerate.amazonaws.com"
    # bucket_name = "cdn-desabasto.s3-accelerate.amazonaws.com"
    aws_location = s3["aws_location"]
    file_name = local_file.split("\\")[-1]
    print("file_name: ", file_name)
    s3_file = f"{aws_location}/{s3_dir}{file_name}"
    print("local_file: ", local_file)
    print("s3_file: ", s3_file)
    try:
        s3_client.upload_file(local_file, bucket_name, s3_file)
        print("Upload Successful")
        print("end time: ", timezone.now())
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except Exception as e:
        print("Error: ", e)
        return False


# from scripts.verified.utils.boto_s3 import upload_s3_files
# upload_s3_files = upload_s3_files(
#     'D:\\RecetasIMSS\\req_mayo_2020_02.txt.gz', 'nacional/imss/202107/')
# f'H:\\Mi unidad\\IMSS\\Noviembre_2021.zip',
def upload_simple():
    files = upload_s3_files(
        f'H:\\Mi unidad\\IMSS\\Enero_2022-1.rar',
        'nacional/imss_imss-bienestar/330018024006508/dvd3/')
    files = upload_s3_files(
        f'H:\\Mi unidad\\IMSS\\Enero_2022-2.rar',
        'nacional/imss_imss-bienestar/330018024006508/dvd3/')


def upload_imss_files():
    file_names = [
        # "2022-1.zip",
        # "2022-2.zip",
        # "2022-3.zip",
        # "2022-4.zip",
        # "2022-5.zip",
        # "2022-6.zip",
        # "2022-7.zip",
        # "2022-8.zip",
        "IMSS_BIENESTAR_330018024006508.zip",
        # "Enero_2024.zip",
    ]
    for file_name in file_names:
        origin_path = f'H:\\Mi unidad\\IMSS\\{file_name}'
        destination_path = 'nacional/imss_imss-bienestar/330018024006508/dvd2/'
        upload_s3_files(origin_path, destination_path)


def upload_imss_year(year="2021"):
    file_names = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    for file_name in file_names:
        final_name = f"{file_name}_{year}.zip"
        origin_path = f'H:\\Mi unidad\\IMSS\\{final_name}'
        destination_path = 'nacional/imss_imss-bienestar/330018024006508/dvd2/'
        upload_s3_files(origin_path, destination_path)


def upload_many_years():
    years = ["2021", "2022", "2023"]
    for year in years:
        upload_imss_year(year)

# H:\Mi unidad\IMSS\Noviembre_2021.zip


# upload_s3_files2 = upload_s3_files(
#     'C:\\Users\\Ricardo\\Downloads\\req_mayo_2020_02.txt.gz', 'nacional/imss/202107/')
