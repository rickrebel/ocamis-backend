
select mu.delegation_name
from med_cat_medicalunit mu

where
    mu.delegation_name is not null
    and mu.delegation_id is null
group by mu.delegation_name



