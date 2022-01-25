
from desabasto.recipe_report_scriptsv2 import massive_upload_csv_to_db
massive_upload_csv_to_db("issste", [2020])


def generate_key2():
    import re
    from desabasto.models import Container
    all_conts = Container.objects.all()
    for cont in all_conts:
        cont.key2 = re.sub(r'(\.)', '', cont.key)
        cont.save()


def clean_old_imports():
    from desabasto.models import (Container, CLUES, RecipeReportLog)
    Container.objects.filter(presentation__isnull=True).delete()
    CLUES.objects.filter(clues__isnull=True).delete()
    RecipeReportLog.objects.all().delete()


TRUNCATE desabasto_recipemedicine2, desabasto_recipereport2, desabasto__medic RESTART IDENTITY

