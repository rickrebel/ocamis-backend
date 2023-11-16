# faltan excepciones
# def get_paths_from_models():
#     from inai.models import (
#         DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
#     from scripts.s3_cleaning.models import (
#         DataFilePath, ReplyFilePath, TableFilePath, SheetFileFilePath)
#     from django.contrib.contenttypes.models import ContentType
#
#     models = [DataFile, ReplyFile, TableFile, SheetFile]
#
#     for model in models:
#         file_models = model.objects.all()
#         for file_model in file_models:
#             content_type = ContentType.objects.get_for_model(file_model)
#             model_name = content_type.model
#             path = set_upload_path(file_model, file_model.file.name)
#             if model_name == "datafile":
#                 DataFilePath.objects.get_or_create(
#                     data_file=file_model, path=path)
#             elif model_name == "replyfile":
#                 ReplyFilePath.objects.get_or_create(
#                     reply_file=file_model, path=path)
#             elif model_name == "sheetfile":
#                 SheetFileFilePath.objects.get_or_create(
#                     sheet_file=file_model, path=path)
#             elif model_name == "tablefile":
#                 TableFilePath.objects.get_or_create(
#                     table_file=file_model, path=path)
# excepciones


# def dummy_path():
#     from inai.models import (
#         DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
#     # from django.contrib.contenttypes.models import ContentType
#
#     dat = SheetFile.objects.first()
#     # path = set_upload_path(dat, dat.file.name)
#     # content_type = ContentType.objects.get_for_model(dat)
#     # model_name = content_type.model
#     # print("path del primer archivo data file: ", path)
#     print("url guardada en el campo file: ", dat.file)
#     # print("Model name: ", model_name)


# def get_paths_from_models():
#     from inai.models import (
#         DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
#     from task.models import FilePath
#
#     # model_mapping = {
#     #     'datafile': (DataFile, DataFilePath),
#     #     'replyfile': (ReplyFile, ReplyFilePath),
#     #     'tablefile': (TableFile, TableFilePath),
#     #     'sheetfile': (SheetFile, SheetFileFilePath),
#     # }
#     # for model_name, (model, path_model) in model_mapping.items():
#     #     file_models = model.objects.all()
#     #
#     #     for file_model in file_models:
#     #         path = set_upload_path(file_model, file_model.file.name)
#     #
#     #         path_model.objects.get_or_create(**{model_name: file_model, 'path': path})
#
#     model_mapping = {
#         'data_file': DataFile,
#         'reply_file': ReplyFile,
#         'sheet_file': SheetFile,
#         'table_file': TableFile
#     }
#     for model_name, model in model_mapping.items():
#         model_instances = model.objects.filter(
#             file__isnull=False, file_paths__isnull=True)
#         for model_instance in model_instances:
#             path = model_instance.file
#             args = {model_name: model_instance, 'path_to_file': path}
#             FilePath.objects.create(**args)

# def find_dummy_file():
#     from inai.models import (
#         DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
#
#     model_mapping = {
#         'data_file': DataFile,
#         'reply_file': ReplyFile,
#         'sheet_file': SheetFile,
#         'table_file': TableFile
#     }
#
#     for model_name, model in model_mapping.items():
#         try:
#             final_obj = model.objects.get(file__icontains="correspondencia 926083.xlsx")
#             print(final_obj.file)
#         except:
#             pass


# def dummy_change_path():
#     import boto3
#     from django.conf import settings
#     from inai.models import (
#         DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
#     from task.models import FilePath
#
#     bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
#     aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
#     aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
#     s3 = boto3.resource(
#         's3', aws_access_key_id=aws_access_key_id,
#         aws_secret_access_key=aws_secret_access_key)
#     my_bucket = s3.Bucket(bucket_name)
#
#     # objs = my_bucket.objects.filter(Prefix="data_files/experiment")
#     # for obj in objs:
#     #     if obj.key == "data_files/experiment/Prac04.pdf":
#     #         my_bucket.copy(
#     #             {'Bucket': bucket_name,
#     #              'Key': 'data_files/experiment/Prac04.pdf'},
#     #             'static/Prac04.pdf')
#
#     objs = my_bucket.objects.filter(Prefix="static/")
#     for obj in objs:
#         if obj.key == "static/Prac04.pdf":
#             # obj.delete()
#
#     # obj = s3.Object(bucket_name, "data_files/experiment/Prac04.pdf")
#     # print(obj)

def get_bucket_files():
    import boto3
    from django.conf import settings
    from inai.models import (
        DataFile, ReplyFile, TableFile, SheetFile, set_upload_path)
    from task.models import FilePath

    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME")
    aws_access_key_id = getattr(settings, "AWS_ACCESS_KEY_ID")
    aws_secret_access_key = getattr(settings, "AWS_SECRET_ACCESS_KEY")
    s3 = boto3.resource(
        's3', aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)
    my_bucket = s3.Bucket(bucket_name)

    excluded_dirs = [
        "admin/", "aws_errors/", "cat_images/", "ckeditor/", "experiment/",
        "logos/", "mat_views/", "profile_images/", "rest_framework/"]

    model_mapping = {
        'data_file': DataFile,
        'reply_file': ReplyFile,
        'sheet_file': SheetFile,
        'table_file': TableFile
    }

    # all_bucket_files = my_bucket.objects.all()
    # all_bucket_files = my_bucket.objects.filter(Prefix="data_files/")
    all_bucket_files = my_bucket.objects.filter(
        Prefix="data_files/estatal/isem/202210")

    for obj in all_bucket_files:
        key = obj.key.replace('data_files/', '')
        if not any(excluded_dir in key for excluded_dir in excluded_dirs):
            # files_to_check.append(obj.key)
            # real_path = "algo"
            final_obj = None
            # alemusp falta size del meta, y ambas rutas
            args = {'path_in_bucket': key, 'size': obj.size}
            for model_name, model in model_mapping.items():
                try:
                    final_obj = model.objects.get(file=key)
                    args[model_name] = final_obj
                    # alemusp comparación de set_upload_path
                    path_in_db = set_upload_path(final_obj, final_obj.file.name)
                    args['path_fo_file'] = path_in_db
                    # alemusp Falta hacer la verificación del formato de ambos
                    args['is_correct_path'] = key == path_in_db
                    print("argumentos a guardar: ", args.items())
                    break
                except:
                    pass

            # FilePath.objects.create(**args)



# test con la carpeta data_files/estatal/isem/202210 y el archivo específico
# correspondencia 926083.xlsx
# argumentos a guardar:  dict_items([
# ('path_in_bucket', 'estatal/isem/202210/correspondencia 926083.xlsx'),
# ('size', 19645),
# ('data_file', <DataFile: estatal/isem/202210/correspondencia 926083.xlsx Instituto de Salud del Estado de México (ISEM) -- 00872 - 683. Reporte de suministros>),
# ('path_fo_file', 'estatal/isem/00872/estatal/isem/202210/correspondencia 926083.xlsx'),
# ('is_correct_path', False)
# ])