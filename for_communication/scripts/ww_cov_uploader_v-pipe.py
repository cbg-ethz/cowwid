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

upload_covspectrum=config["upload_covspectrum"]
upload_wisedb=config["upload_wisedb"]
upload_polybox=config["upload_polybox"]

################################  Upload to Cov-Spectrum ################################
if upload_covspectrum == True:

    dbhost = (
        "gs-db-1.int.genspectrum.org" #"s0.int.genspectrum.org" # "db-lapis.cuupxsogkmvx.eu-central-1.rds.amazonaws.com"  #'id-hdb-psgr-cp61.ethz.ch'
    )
    # load from netrc
    dbuser, dbpass = netrc.netrc().authenticators(dbhost)[0::2] # here is need a netrc file: it should be in the home folder of the user - add the login for covspetrum as an other element in the .netrc on pangolin euler home folder

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
    
    locations = sorted(list(update_data_for_cov_spectrum.keys()))
    variants = sorted(
        list({v for loc_data in update_data_for_cov_spectrum.values() for v in loc_data.keys()})
    )

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

    ## Save to DB !
    dbconn.commit()

    cur.close()
    dbconn.close()


################################  Upload to WiseDB ################################
if upload_wisedb == True :
        
    input_file = config["output_for_wiseDB"] 
    output_file = config["WiseDB_output_file_gz"]
    checksum_file = config["WiseDB_checksum_file"]
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

    dbhost = (
        "wisedb"
    )
    # load from netrc
    dbuser, token = netrc.netrc().authenticators(dbhost)[0::2] # add the login for covspetrum as an element in the .netrc

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
if upload_polybox == True:
        
    polybox_url = config["FOPH_BAG_polybox_url"]

    subprocess.run([
        "curl", "--netrc", "--upload-file", update_data_combined_file, polybox_url
    ])
    subprocess.run([
        "curl", "--netrc", "--upload-file", reformatted, polybox_url
    ])

    ################################ Upload to Public Polybox folder ################################
    polybox_url = config["Public_polybox_url"]

    subprocess.run([
        "curl", "--netrc", "--upload-file", update_data_combined_file, polybox_url
    ])
