
def zip_experiments():
    import zipfile
    import datetime
    url = "C:\\Users\\Ricardo\\dev\\desabasto\\desabasto-api\\fixture\\zipfolder.zip"

    #directory = self.file.url
    directory = url
    #path_imss_zip = "C:\\Users\\Ricardo\\recetas grandes\\Recetas IMSS\\Septiembre-20220712T233123Z-001.zip"
    #zip_file = zipfile.ZipFile(self.file.url)
    zip_file = zipfile.ZipFile(url)
    all_files = zip_file.namelist()
    print(all_files)
    for curr_file in all_files:
        print(curr_file)

    with zipfile.ZipFile(url, mode="r") as archive:
        for info in archive.infolist():
            print(f"Es directorio: {info.is_dir()}")
            print(f"Filename: {info.filename}")
            print(f"Modified: {datetime.datetime(*info.date_time)}")
            print(f"Normal size: {info.file_size} bytes")
            print(f"Compressed size: {info.compress_size} bytes")
            print("-" * 20)
        archive.close()

    #with zipfile.ZipFile(self.url, 'r') as zip_ref:
    with zipfile.ZipFile(url, 'r') as zip_ref:
        zip_ref.extractall(directory)               
    #ZipFile.extractall(path=None, members=None, pwd=None)   
    #for f in os.listdir(directory):
    for f in all_files:
        new_file = self
        new_file.pk = None
        new_file = DataFile.objects.create(
            file="%s%s" % (directory, f),
            origin_file=self,
            date=self.date,
            status=initial_status,
            #Revisar si lo más fácil es poner o no los siguientes:
            file_control=file_control,
            petition=self.petition,
            petition_month=file.petition_month,
            )
    self = new_file
    suffixes.remove('.zip')
