from inai.models import Petition
from respond.models import ReplyFile, DataFile


class DividePetition:
    def __init__(self, folio_petition: str, years: list):
        self.petition = Petition.objects.filter(folio_petition=folio_petition).first()
        self.petition_id = self.petition.id
        self.folio_petition = folio_petition
        self.years = years

    def divide(self):
        if self.petition is None:
            return None

        for year in self.years:
            self.petition = Petition.objects\
                .filter(folio_petition=self.folio_petition).first()
            year_month_records = self.petition.month_records.filter(
                year_month__startswith=f"{year}-")
            new_folio = f"{self.folio_petition}+{year}"
            petition = self.petition
            petition.pk = None
            petition.folio_petition = new_folio
            petition.id_inai_open_data = None
            petition.save()
            petition.month_records.clear()
            for month_record in year_month_records:
                petition.month_records.add(month_record)
            petition.save()
            reply_files = ReplyFile.objects.filter(
                petition_id=self.petition_id, file__icontains=year)
            reply_files.update(petition=petition)
            reply_files = ReplyFile.objects.filter(petition=petition)
            # print("reply_files", reply_files)
            data_files = DataFile.objects.filter(reply_file__in=reply_files)
            pfcs = data_files.values_list("petition_file_control", flat=True)
            pfcs = list(set(pfcs))
            print("pfcs", pfcs)
            # for pfc_id in pfcs:
            #     current_data_files = DataFile.objects.filter(
            #         petition_file_control_id=pfc_id)
            #     pfc = PetitionFileControl.objects.get(id=pfc_id)
            #     new_pfc = pfc
            #     new_pfc.pk = None
            #     new_pfc.petition = petition
            #     new_pfc.save()
            #     current_data_files.update(petition_file_control=new_pfc)

    def revert(self):
        self.petition = Petition.objects.filter(folio_petition=self.folio_petition).first()
        for year in self.years:
            new_folio = f"{self.folio_petition}+{year}"
            petition = Petition.objects.filter(folio_petition=new_folio).first()
            reply_files = ReplyFile.objects.filter(petition=petition)
            reply_files.update(petition=self.petition)
            petition.delete()


# x = DividePetition("0063700513521", ["2017", "2018"])
#
# x.divide()

# x.revert()

