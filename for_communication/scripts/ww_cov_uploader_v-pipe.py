import gzip
import shutil
import hashlib
import subprocess
import numpy as np
import seaborn as sns
import pandas as pd
import yaml
import json
from tqdm import tqdm, trange
import time
import datetime
import os
import sys
import netrc
import psycopg2
from copy import deepcopy


################################ Globals ################################

# Load YAML config
with open("/cluster/project/pangolin/cowwid/for_communication/config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Access variables
update_data_combined_file = config["update_data_combined_file"]
blacklist = config["blacklist"]
update_data_covspectrum_file = config["update_data_covspectrum_file"]
reformatted = config["reformatted"]

################################  Upload to Cov-Spectrum ################################
dbhost = (
    "gs-db-1.int.genspectrum.org" #"s0.int.genspectrum.org" # "db-lapis.cuupxsogkmvx.eu-central-1.rds.amazonaws.com"  #'id-hdb-psgr-cp61.ethz.ch'
)
# load from netrc
dbuser, dbpass = netrc.netrc().authenticators(dbhost)[0::2]

dbconn = psycopg2.connect(
    host=dbhost,
    database="covspectrum",  #'sars_cov_2',
    user=dbuser,
    password=dbpass,
    port="5432",
)
cur = dbconn.cursor()

with open(update_data_covspectrum_file, "r") as f:
    update_data_for_cov_spectrum = json.load(f)


for loc in tqdm(locations, desc="Locations", position=0):
    for pango in tqdm(variants, desc=loc, position=1, leave=True):
        cur.execute(
            """
            DO $$
            BEGIN
             IF EXISTS (SELECT ww.data FROM public.wastewater_result AS ww WHERE ww.variant_name=%(var)s AND ww.location=%(city)s) THEN
              UPDATE public.wastewater_result AS ww SET data=%(data)s WHERE ww.variant_name=%(var)s AND ww.location=%(city)s;
             ELSE
              INSERT INTO public.wastewater_result (variant_name, location, data)
              VALUES(%(var)s, %(city)s, %(data)s);
             END IF;
            END
            $$
            """,
            {
                "data": json.dumps(update_data_for_cov_spectrum[loc][pango]).replace("NaN", "null"),
                "var": pango,
                "city": loc,
            },
        )


## Abort DB update !
#dbconn.rollback()

## Save to DB !
dbconn.commit()

cur.close()
dbconn.close()


################################  Upload to WiseDB ################################

input_file = config["update_data_combined_file"]
output_file = config["WiseDB_output_file"]
checksum_file = config["WiseDB_checksum_file"]
token_file_path = config["WiseDB_token_file_path"]
url = config["WiseDB_url"]

# gz compress the curves json file. --best is required for it to be compliant with 
with open(input_file, 'rb') as f_in, gzip.open(output_file, 'wb', compresslevel=9) as f_out:
    shutil.copyfileobj(f_in, f_out)

# md5 checksum of the zipped file. wisedb will test to ensure the correct file is uploaded
def compute_sha256(file_path, chunk_size=8192):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

checksum = compute_sha256(output_file)
with open(checksum_file, 'w') as f:
    f.write(checksum + '\n')
    
# Setting up credentials
with open(token_file_path, 'r') as token_file:
    token = token_file.read().strip()

# upload
curl_command = [
    "curl",
    url,
    "-H", f"Authorization: Token {token}",
    "-F", f"checksums={checksum}",
    "-F", f"files=@{output_file}"
]

result = subprocess.run(curl_command, capture_output=True, text=True)

print("Response:")
print(result.stdout)
if result.stderr:
    print(result.stderr)


################################ Upload to FOPH/BAG's Polybox ################################

polybox_url = config["FOPH_BAG_polybox_url"]

%%bash -s "$polybox_url" "$update_data_combined_file" "$reformatted"
ls -l "$2"
curl --netrc --upload-file "$2" "$1" 
curl --netrc --upload-file "$3" "$1"

################################ Upload to Public Polybox folder ################################
polybox_url = config["Public_polybox_url"]
%%bash -s "$polybox_url" "$update_data_combined_file" "ww_update_data_combined.json"
ls -l "$2"
curl --netrc --upload-file "$2" "$1" 
curl --netrc --upload-file "$3" "$1"