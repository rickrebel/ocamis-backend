
import json


class DataUtilsMix:

    def save_errors(self, errors, error_name):
        from rest_framework.response import Response
        from rest_framework import (permissions, views, status)        
        from category.models import StatusControl

        #errors = ['No se pudo descomprimir el archivo gz']
        curr_errors = self.error_process or []
        curr_errors += errors
        print("error_name", error_name)
        current_status, created = StatusControl.objects.get_or_create(
            name=error_name, group="process")
        self.error_process = curr_errors
        self.status_process = current_status 
        print(curr_errors)
        self.save()
        return Response(
            {"errors": errors}, status=status.HTTP_400_BAD_REQUEST)


    def massive_insert_copy(self, errors, error_name):
        return 2
        #guardo esto para considerarlo en "missing_rows":
        """
        MissingRow.objects.create(
            file=file,
            original_data=row_data,
            row_seq=row_seq,
            errors=["Conteo distinto de Columnas %s" % len(row_data)],
        )"""