from scripts.s3_cleaning.clean_bucket import CleanBucket


x = CleanBucket(aws_location="data_files/aws_errors")
x. exluded_dirs = []
x.get_files_in_s3()
x.report_orphans()
