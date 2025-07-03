"""
Script Name: ww_cov_curves_v-pipe.py

Original Authors:
    - Ivan Topolsky (@DrYak)
    - David Dreifuss (@dr-david)
    - Matteo Carrara (@mcarrara-bioinfo)

Description:
    This script processes and visualizes smoothed time-series data on SARS-CoV-2 variant proportions across 
    Swiss locations.

Maintainer:
    - Kyra Kirschenbuehler (@kirschen-k)
"""

import matplotlib.pyplot as plt
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
datadir = config["datadir"]
jsonfile_smooth = config["jsonfile_smooth"]
plots_dir = config["plots_dir"]
color_map = config["color_map"]
blacklist = config["blacklist"]
update_data_file = config["update_data_file"]
update_data_combined_file = config["update_data_combined_file"]
update_data_covspectrum_file = config["update_data_covspectrum_file"]
reformatted = config["reformatted"]

################################ Data ################################
# Smoothed curves
print(
    f"reusing {jsonfile_smooth} last modified: {time.ctime(os.path.getmtime(jsonfile_smooth))}"
)

with open(jsonfile_smooth, "r") as file:
    update_data_smooth = json.load(file)

## extra snippet to remove specific variants from the curves after lollipop processing
#for k,v in update_data_smooth.items():
#    del update_data_smooth[k]["BA.2.87.1"]
#update_data_smooth["Altenrhein (SG)"].keys()

# Locations list in smooth
locations_file = list({c for c in update_data_smooth.keys()})


# Date max (useful for the e-mail)
for l in locations_file:
    print(
        l,
        max(
            [
                d["date"]
                for v in update_data_smooth[l].values()
                for d in v["timeseriesSummary"]
            ]
        ),
        sep="\t",
    )

# date sentence in e-mail
lastdates = {
    l: max(
        [
            d["date"]
            for v in update_data_smooth[l].values()
            for d in v["timeseriesSummary"]
        ]
    )
    for l in locations_file
}
bydates = {d: [] for d in sorted(list(set(lastdates.values())))}
for l, d in lastdates.items():
    bydates[d] += [l]
for d, ls in bydates.items():
    print(
        f"{datetime.datetime.strptime(d, '%Y-%m-%d').date().strftime('%B %d')} for {', '.join(sorted(ls))}."
    )


# this next line clips the plots from a given date
# used for cities which don't want report before a given date
# or for variants that we only report after a given date
only_start_from = {
    "Kanton Zürich": "2021-08-15",  # start_date
    "Lausanne (VD)": "2023-01-01",
    "Basel (BS)": "2024-02-01",
    # 'B.1.1.529':'2021-10-05',
}
print(only_start_from)

update_data = {}
# HACK presume that the smoothing data is the exact set that we want to upload
locations_upload = locations_file
variants_upload = sorted(
    list({v for c in update_data_smooth.values() for v in c.keys()})
)
for loc in tqdm(locations_upload, desc="Locations", position=0):
    update_data[loc] = {}
    for var in tqdm(variants_upload, desc=loc, position=1, leave=False):
        # NOTE we always junk the heatmap, it's not up to date anyway
        update_data[loc][var] = {
            # "updateDate": todaydate,
            "timeseriesSummary": [
                x
                for x in update_data_smooth[loc][var]["timeseriesSummary"]
                if ((loc not in only_start_from) or (x["date"] >= only_start_from[loc]))
                and (
                    (var not in only_start_from) or (x["date"] >= only_start_from[var])
                )
            ],
            "mutationOccurrences": (np.nan),
        }

################################ Inspect ################################
# Locations list in smooth
locations = sorted(list({c for c in update_data.keys()}))

# Variants in smooth
variants = sorted(list({v for c in update_data.values() for v in c.keys()}))


# Does each one of them has a color?
missing_color = list(set(variants) - set(color_map.keys()))
print(", ".join(missing_color))
assert 0 == len(missing_color), "ERROR: some variant without color !"

# Load in a dataframe
df = pd.DataFrame.from_records(
    data=[
        {
            "location": loc,
            "date": pd.to_datetime(d["date"]),
            "variant": var,
            "proportion": d["proportion"],
            "upper": d["proportionUpper"],
            "lower": d["proportionLower"],
        }
        for loc in tqdm(locations_upload, desc="Locations", position=0)
        for var in tqdm(variants_upload, desc=loc, position=1, leave=False)
        for d in update_data_smooth[loc][var]["timeseriesSummary"]
    ]
)
################################ Plot ################################
plotwidth = 40

fig, axes = plt.subplots(
    nrows=3, ncols=2, figsize=(plotwidth, plotwidth / 2), sharex=True
)
axes = axes.flatten()

for i, loc in enumerate(tqdm(locations, desc="Locations", position=0, leave=False)):
    axes[i].set_title(loc)

    for var in tqdm(variants, desc=loc, position=1, leave=False):
        tt_df = (
            df[(df["variant"] == var) & (df["location"] == loc)]
            .sort_values(by=["date"])
            .fillna(0)
        )
        if tt_df.size == 0:
            continue
        tt_df = tt_df.iloc[-15:]
        g = sns.lineplot(
            x=tt_df["date"],
            y=tt_df["proportion"],
            hue=tt_df["variant"],
            ax=axes[i],
            palette=color_map,
        )
        g.get_legend().remove()
        axes[i].fill_between(
            x=tt_df["date"],
            y1=np.clip(tt_df["upper"], 0.0, 1.0),
            y2=np.clip(tt_df["lower"], 0.0, 1.0),
            alpha=0.2,
            # color="grey",
            color=color_map[var],
        )
handles, labels = axes[i].get_legend_handles_labels()
fig.legend(
    handles, labels, loc="lower center", ncol=len(labels), bbox_to_anchor=(0.5, 0.05)
)
fig.suptitle(f"Deconvolution by V-pipe")
plt.savefig(os.path.join(plots_dir, f"combined-vpipe.pdf"))
plt.savefig(os.path.join(plots_dir, f"combined-vpipe.svg"))
plt.savefig(os.path.join(plots_dir, f"combined-vpipe.png"))

with open(update_data_combined_file, "w") as file:
    file.write(
        json.dumps(update_data).replace("NaN", "null")
    )  # syntactically standard compliant JSON vs. python numpy's output.


################################ Data Preparation for Upload to Cov-Spectrum ################################

update_data_for_cov_spectrum = deepcopy(update_data)
for entry in blacklist:
    blacklist_location = entry["location"]
    blacklist_date = entry["date"]
    blacklist_reason = entry["reason"]
    for k in update_data_for_cov_spectrum[blacklist_location].keys():
        dates = update_data_for_cov_spectrum[blacklist_location][k]["timeseriesSummary"]
        for date in dates:
            if date["date"] == blacklist_date:
                update_data_for_cov_spectrum[blacklist_location][k]["timeseriesSummary"].remove(date)
print("Data Preparation for Upload to Cov-Spectrum:")
print("Blacklisted: "+str(len(blacklist)))
print(len(update_data[blacklist_location][k]["timeseriesSummary"]))
print(len(update_data_for_cov_spectrum[blacklist_location][k]["timeseriesSummary"]))

with open(update_data_covspectrum_file, "w") as file:
    file.write(
        json.dumps(update_data_for_cov_spectrum).replace("NaN", "null")
    )  # syntactically standard compliant JSON vs. python numpy's output.


################################ Data Preparation for Upload to FOPH/BAG's Polybox ################################

reformat = {
    var: {
        loc: {"timeseriesSummary": update_data[loc][var]["timeseriesSummary"]}
        for loc in tqdm(locations, desc=pango, position=1, leave=False)
    }
    for pango in tqdm(variants, desc="Variants", position=0)
}

# CHECK: print first entry to check if is formatted correctly:
# Get first variant and location
first_variant = next(iter(reformat))
first_location = next(iter(reformat[first_variant]))

# Print nicely formatted JSON
print(json.dumps(
    reformat[first_variant][first_location],
    indent=2
))

with open(reformatted, "w") as file:
    file.write(
        json.dumps(reformat).replace("NaN", "null")
    )  # syntactically standard compliant JSON vs. python numpy's output.