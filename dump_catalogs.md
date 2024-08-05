Importante, hay que crear la carpeta fixture/db, o las carpetas de destino, el comando no puede crear carpetas si el path destino no existe.

clues y delegacion pueden causar conflictos al cargar los datos, revisar los fixtures generados.

Provider depende de:

    python -Xutf8 .\manage.py dumpdata auth.User --indent 4 > fixture/db/auth_user.json
    python .\manage.py dumpdata auth.User --indent 4 > fixture/db/auth_user.json


comandos para extraer los datos de los catalogos en sus fixtures:


    python .\manage.py dumpdata med_cat.Delivered --indent 4 > fixture/db/med_cat.json

    python .\manage.py dumpdata respond.Behavior --indent 4 > fixture/db/respond.json

    python .\manage.py dumpdata category.StatusControl category.FileType category.FileFormat category.ColumnType category.DateBreak --indent 4 > fixture/db/category.json

    python .\manage.py dumpdata geo.State geo.Municipality geo.Institution geo.Typology geo.Provider geo.CLUES geo.Delegation geo.Jurisdiction geo.Agency --indent 4 > fixture/db/geo.json

    python .\manage.py dumpdata classify_task.StatusTask classify_task.TaskFunction classify_task.Stage --indent 4 > fixture/db/classify_task.json

    python .\manage.py dumpdata data_param.DataGroup data_param.Collection data_param.DataType data_param.ParameterGroup data_param.FinalField data_param.CleanFunction --indent 4 > fixture/db/data_param.json

    python .\manage.py dumpdata medicine.Source medicine.Group medicine.Component medicine.PresentationType medicine.Presentation medicine.Container --indent 4 > fixture/db/medicine.json

    python .\manage.py dumpdata transparency.Anomaly transparency.TransparencyIndex transparency.TransparencyLevel --indent 4 > fixture/db/transparency.json

    python .\manage.py dumpdata rds.Platform rds.Cluster rds.MatView rds.OperationGroup rds.Operation --indent 4 > fixture/db/rds.json


Comando general (antiguo para referencias)

    python ./manage.py dumpdata --exclude auth --exclude contenttypes --exclude authtoken --exclude admin.LogEntry --exclude sessions --indent 2 -v 2  > fixture/todo_desabasto.json

    python -Xutf8 ./manage.py dumpdata auth authtoken --exclude auth.permission --indent 2 -v 2  > fixture/auth_ocamis_prod_1.json
    python -Xutf8 ./manage.py dumpdata --exclude auth --exclude contenttypes --exclude authtoken --exclude sessions --exclude admin.LogEntry --exclude formula --exclude med_cat --indent 2 > fixture/todo_ocamis_1.json



    python -Xutf8 ./manage.py dumpdata auth authtoken --exclude auth.permission --indent 2 -v 2  > fixture/auth_yeeko_prod_4.json
