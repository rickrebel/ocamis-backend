def get_bucket_files():
    import boto3
    import time
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

    model_dicts = {
        'data_file': dict(),
        'reply_file': dict(),
        'sheet_file': dict(),
        'table_file': dict()
    }

    for model_name, model in model_mapping.items():
        model_objects = model.objects.exclude(file='')
        for model_obj in model_objects:
            args = {model_obj.file.name: model_obj.id}
            model_dicts[model_name].update(args)

    # all_bucket_files = my_bucket.objects.all()
    all_bucket_files = my_bucket.objects.filter(Prefix="data_files/")
    # all_bucket_files = my_bucket.objects.filter(
    #     Prefix="data_files/estatal/isem/202210")
    counter = 0
    objs_to_save = []
    start_time = time.time()

    for obj in all_bucket_files:
        key = obj.key.replace('data_files/', '')
        if not any(excluded_dir in key for excluded_dir in excluded_dirs):
            final_obj = None
            args = {'path_in_bucket': key, 'size': obj.size,
                    'is_correct_path': False, 'reply_file_id': None,
                    'data_file_id': None, 'sheet_file_id': None,
                    'table_file_id': None}
            for model_name, dicc in model_dicts.items():
                model_id = dicc.get(key)
                if model_id is None:
                    continue
                args[f"{model_name}_id"] = model_id
                args['path_to_file'] = key
                args['is_correct_path'] = True
                # print("argumentos a guardar: ", args.items())
                # counter += 1
                created_obj = FilePath(path_in_bucket=args['path_in_bucket'],
                                       path_to_file=args['path_to_file'],
                                       reply_file_id=args['reply_file_id'],
                                       data_file_id=args['data_file_id'],
                                       sheet_file_id=args['sheet_file_id'],
                                       table_file_id=args['table_file_id'],
                                       is_correct_path=args['is_correct_path'],
                                       size=args['size'])
                objs_to_save.append(created_obj)
                if len(objs_to_save) == 1000:
                    FilePath.objects.bulk_create(objs_to_save)
                    objs_to_save.clear()
            # for model_name, model in model_mapping.items():
            #     try:
            #         final_obj = model.objects.get(file=key)
            #         args[model_name] = final_obj
            #         # path_in_db = set_upload_path(final_obj, final_obj.file.name)
            #         # args['path_to_file'] = path_in_db
            #         args['path_to_file'] = final_obj.file.name
            #         # args['is_correct_path'] = key == path_in_db
            #         args['is_correct_path'] = key == final_obj.file.name
            #         # print("argumentos a guardar: ", args.items())
            #
            #         break
            #     except:
            #         pass

            # FilePath.objects.create(**args)
        counter += 1
        if counter == 100000:
            break

    FilePath.objects.bulk_create(objs_to_save)

    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Tiempo de ejecución: {execution_time} segundos")


def clean_file_path():
    from task.models import FilePath
    FilePath.objects.all().delete()


def dummy_dicts():
    from inai.models import (
        DataFile, ReplyFile, TableFile, SheetFile)

    model_mapping = {
        'data_file': DataFile,
        'reply_file': ReplyFile,
        'sheet_file': SheetFile,
        'table_file': TableFile
    }

    model_dicts = {
        'data_file': dict(),
        'reply_file': dict(),
        'sheet_file': dict(),
        'table_file': dict()
    }

    for model_name, model in model_mapping.items():
        model_objects = model.objects.exclude(file='')
        for model_obj in model_objects[:3]:
            args = {model_obj.file.name: model_obj.id}
            model_dicts[model_name].update(args)

    # for model_name, dicc in model_dicts.items():
    #     print(f"modelo: {model_name}, tam del dicc: {len(dicc)}")

    for model_name, dicc in model_dicts.items():
        print(f"model: {model_name}")
        for file, id in dicc.items():
            print(f"file: {file}, id: {id}")



# test con la carpeta data_files/estatal/isem/202210 y el archivo específico
# correspondencia 926083.xlsx
# argumentos a guardar:  dict_items([
# ('path_in_bucket', 'estatal/isem/202210/correspondencia 926083.xlsx'),
# ('size', 19645),
# ('data_file', <DataFile: estatal/isem/202210/correspondencia 926083.xlsx Instituto de Salud del Estado de México (ISEM) -- 00872 - 683. Reporte de suministros>),
# ('path_fo_file', 'estatal/isem/00872/estatal/isem/202210/correspondencia 926083.xlsx'),
# ('is_correct_path', False)
# ])
