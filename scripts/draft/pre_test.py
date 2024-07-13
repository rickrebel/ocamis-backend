

def build_required_catalogs():
    from med_cat.models import Delivered
    from respond.models import Behavior
    from geo.models import (
        State, Municipality, Institution, Typology, Provider,
        CLUES, Delegation, Jurisdiction, Agency)
    from category.models import (
        StatusControl, FileType, FileFormat, ColumnType, DateBreak)
    from classify_task.models import StatusTask, TaskFunction, Stage
    from data_param.models import (
        DataGroup, Collection, DataType, ParameterGroup, FinalField,
        CleanFunction)
    from medicine.models import (
        Source, Group, Component, PresentationType, Presentation, Container)
    from transparency.models import Anomaly, TransparencyIndex, TransparencyLevel
    from rds.models import (
        Platform, Cluster, MatView, OperationGroup, Operation)

    from scripts.verified.initial_fields import WeeksGenerator
    # Revisar antes si basta con que en Provider se generen
    # Función build MonthRecord and WeekRecord (WeeksGenerator)


############################
# TESTS QUE SE DEBERÁN HACER:
############################


# ## TEST DE FUNCIONES ANIDADAS:

# Mandar a llamar una función que tenga funciones hijas anidadas y
# que tengan funciones "after" con nombres específicos y normales
# (terminados en after). Que alguna de las tareas tenga finished_function
# Hacer un mix entre tareas que se ejecuten en Lambda y otras que
# no vayan a Lambda.


# ## TEST DE DESCOMPRESIÓN:

# Crear solicitud para el provider IMSS acronym = 'IMSS (Ordinario)'
# Agregar un reply_file con un archivo con muchos tipos de descompresión:
# Archivos .zip y .rar con carpetas en distintos niveles y con archivos
# comprimidos, archivos vacíos, comprimidos vacíos, etc.


