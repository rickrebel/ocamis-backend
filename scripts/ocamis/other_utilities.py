from inai.models import NameColumn
from data_param.models import FinalField

def join_fields():
    all_names = NameColumn.objects.filter(final_field__verbose_name__startswith="!")

    for name_col in all_names:
        real_name = name_col.final_field.verbose_name[1:]
        #print("----------")
        #print(name_col.final_field.verbose_name)
        #print(real_name)
        correct_final_field = FinalField.objects.get(
            verbose_name=real_name, 
            parameter_group=name_col.final_field.parameter_group)
        name_col.final_field = correct_final_field
        name_col.save()
        print(name_col)




def re_suffixes():
    import re
    lines = [".xls", ".doc", ".zip", ".HG", ".11", ".docso"]
    re_is_suffix = re.compile(r'^\.(\w{3,4})$')

    for line in lines:
        print(line)
        is_suffix = bool(re.search(re_is_suffix, line))
        print(is_suffix)
        print("-----------")

