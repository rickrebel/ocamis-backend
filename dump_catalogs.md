Importante, hay que crear la carpeta fixtures, o las carpetas de destino, el comando no puede crear carpetas si el path destino no existe.

clues y delegacion pueden causar conflictos al cargar los datos, revisar los fixtures generados.

provider depende de:

    python manage.py dumpdata auth.User --indent 4 > fixtures/auth_user.json


comandos para extraer los datos de los catalogos en sus fixtures:


    python .\manage.py dumpdata med_cat.Delivered --indent 4 > fixtures/med_cat.json

    python .\manage.py dumpdata respond.Behavior --indent 4 > fixtures/respond.json

    python .\manage.py dumpdata category.StatusControl category.FileType category.FileFormat category.ColumnType category.DateBreak --indent 4 > fixtures/category.json

    python .\manage.py dumpdata geo.State geo.Municipality geo.Institution geo.Typology geo.Provider geo.CLUES geo.Delegation geo.Jurisdiction geo.Agency --indent 4 > fixtures/geo.json

    python .\manage.py dumpdata classify_task.StatusTask classify_task.TaskFunction classify_task.Stage --indent 4 > fixtures/classify_task.json

    python .\manage.py dumpdata data_param.DataGroup data_param.Collection data_param.DataType data_param.ParameterGroup data_param.FinalField data_param.CleanFunction --indent 4 > fixtures/data_param.json

    python .\manage.py dumpdata medicine.Source medicine.Group medicine.Component medicine.PresentationType medicine.Presentation medicine.Container --indent 4 > fixtures/medicine.json

    python .\manage.py dumpdata transparency.Anomaly transparency.TransparencyIndex transparency.TransparencyLevel --indent 4 > fixtures/transparency.json

    python .\manage.py dumpdata rds.Platform rds.Cluster rds.MatView rds.OperationGroup rds.Operation --indent 4 > fixtures/rds.json

