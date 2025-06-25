import numpy as np
import pandas as pd
import geopandas as gpd
import seaborn as sns
import yaml

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.patheffects as PathEffects

from adjustText import adjust_text

################################ Globals ################################
# Load YAML config
with open("/cluster/project/pangolin/cowwid/for_communication/config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Access variables
plots_dir = config["plots_dir"]
deconvolution = config["deconvolution"]
switzerland_file = config["switzerland_map"]
kantons_file = config["kantons_map"]
swiss_cities = config["swiss_cities"]
swiss_lakes = config["swiss_lakes"]
swiss_municipalities = config["swiss_municipalities"]
wastewater_plants = config["wastewater_plants"]
legend_information = config["legend_information"]
ARA_2014_SWW = config["ARA_2014_SWW"]
ARA_Einzugsgebiet_2014_SWW = config["ARA_Einzugsgebiet_2014_SWW"]
Ang_Einwohner_ARA_am01012021 = config["Ang_Einwohner_ARA_am01012021"]

color_map = config["color_map"]

blacklist = []

df_lollipop = pd.read_csv(deconvolution, sep="\t",)

df_lollipop['date'] = pd.to_datetime(df_lollipop['date'])
df_lollipop = df_lollipop.rename(columns={"location": "ARA_Name"})

most_recent = max(df_lollipop['date'])
print(most_recent)
df_lollipop.head()

week_before = most_recent - pd.DateOffset(days=7)

#####
#most_recent_basel = pd.to_datetime("2024-12-16")
#week_before_basel = most_recent_basel - pd.DateOffset(days=7)
#df_week = df_lollipop[(df_lollipop['date'] >= week_before) | (df_lollipop['date'] >= week_before_basel)]
#####

df_week = df_lollipop[df_lollipop['date'] >= week_before]
df_week = pd.DataFrame(df_week.groupby(['ARA_Name', 'variant'])['proportion'].agg('mean'))
#df_week.reset_index()

## name for the file
file_out_name = most_recent

df_week = df_week.rename(columns={"proportion": "fraction"})
df_fractions = df_week

print(f"Most recent: {most_recent}")
print(f"Week before: {week_before}")

################################ Read Data ################################
#Obtained from https://github.com/interactivethings/swiss-maps and https://simplemaps.com/data/ch-cities

#switzerland
print("switzerland")
df_switzerland = gpd.read_file(switzerland_file)
df_switzerland.set_crs(epsg=4326, inplace=True)

df_switzerland.head()

#kantons_file
print("kantons")
df_kantons = gpd.read_file(kantons_file)
df_kantons.set_crs(epsg=4326, inplace=True)

df_kantons.head()

#swiss_cities
print("swiss_cities")
tmp = pd.read_csv(swiss_cities)
df_cities = gpd.GeoDataFrame(
    tmp, geometry=gpd.points_from_xy(tmp["lng"], tmp["lat"])
).drop(["lat", "lng"], axis=1)
df_cities.set_crs(epsg=4326, inplace=True)

df_cities.head()

#swiss_lakes
print("swiss_lakes")
df_lakes = gpd.read_file(swiss_lakes)
df_lakes.set_crs(epsg=4326, inplace=True)

df_lakes.head()

#swiss_municipalities
print("swiss_municipalities")
df_munci = gpd.read_file(swiss_municipalities)
df_munci.set_crs(epsg=4326, inplace=True)

df_munci.head()

#wastewater_plants
print("wastewater_plants")
tmp = pd.read_csv(wastewater_plants)
df_plants = gpd.GeoDataFrame(
    tmp, geometry=gpd.points_from_xy(tmp["longitude"], tmp["latitude"])
).drop(["latitude", "longitude"], axis=1)
df_plants.set_crs(epsg=4326, inplace=True)

print(df_plants)

#legend_information
print("legend_information")
df_legend = pd.read_csv(legend_information)

for col in df_legend.columns:
    if col == "population":
        df_legend[col] = df_legend[col].astype(pd.Int64Dtype())

print(df_legend)

################################ Wastewater Catchment Areas ################################
################################ Read geographic data
print("ARA_2014_SWW")
df_ww = gpd.read_file(ARA_2014_SWW)
df_ww.to_crs(epsg=4326, inplace=True)
df_ww.head()

# Einzugsgebiet
print("Einzugsgebiet")
df_ca = gpd.read_file(ARA_Einzugsgebiet_2014_SWW)
df_ca.to_crs(epsg=4326, inplace=True)
df_ca.head()

################################ Read "numeric" data
print("Ang_Einwohner_ARA_am01012021")
df_pop = pd.read_excel(Ang_Einwohner_ARA_am01012021)
df_pop["ARANAME"].replace(
    {
        "SENSETAL (LAUPEN)": "LAUPEN(SENSETAL)",
        "Thal - Altenrhein": "THAL/ALTENRHEIN",
        "Chur": "CHUR",
        "BIOGGIO (LUGANO)": "BIOGGIO(LUGANO)",
    },
    inplace=True,
)
df_pop.set_index("ARANAME", inplace=True)
df_pop.head()

################################ Select relevant CAs
selected_ca_list = [
    #'ARA REGION BERN AG',
    #'PORRENTRUY(SEPE)',
    'BASEL',
    #'SCHWYZ', 
    'LAUPEN(SENSETAL)',
    #'LAUSANNE',
    #'NEUCHATEL',
    #'ZUCHWIL(SOLOTH.-EMME)',
    #'EMMEN(BUHOLZ)',
    #'THAL/ALTENRHEIN',
    'ZUERICH(WERDHOELZLI)',
    'CHUR',
    'BIOGGIO(LUGANO)',
    'VERNIER/AIRE',
    #'SIERRE/NOES',
]

################################ Create plot ################################
Ara_shortnames_dict = config["ara_shortnames"]
Ara_shortnames_dict = {v: k for k, v in Ara_shortnames_dict.items()}
print(Ara_shortnames_dict)

Ara_shortnames_dict_english = config["ara_shortnames_english"]
print(Ara_shortnames_dict_english)

offsets = {'ARA REGION BERN AG': (0,-0.15),
 'PORRENTRUY(SEPE)': (-0.6,0),
 'BASEL': (0.02,0),
 'SCHWYZ': (0,0),
 'LAUPEN(SENSETAL)': (-0.35,-0.3),
 'LAUSANNE': (-0.6,0),
 'NEUCHATEL': (-0.55,0),
 'ZUCHWIL(SOLOTH.-EMME)': (0,0),
 'EMMEN(BUHOLZ)': (-0.3,-0.3),
 'THAL/ALTENRHEIN': (0,0),
 'ZUERICH(WERDHOELZLI)': (0.05,0),
 'CHUR': (0,0),
 'BIOGGIO(LUGANO)': (0.05,0),
 'VERNIER/AIRE': (0.1,-0.1)}
 
x = 0.05
filtered_df = df_fractions.groupby('variant').filter(lambda group: group['fraction'].sum() > x)

# MAKE PLOT

s = 8
fig, ax = plt.subplots(figsize=(1.5 * s, s))

# plot features
df_kantons.boundary.plot(ax=ax, color="grey", alpha=0.2)
df_switzerland.boundary.plot(ax=ax, color="black")
df_lakes.plot(ax=ax, alpha=0.2)

df_ca_sel = df_ca[df_ca["ARA_Name"].isin(selected_ca_list)]
df_ca_sel.plot(ax=ax, color="#333333", alpha=0.25)
df_ca_sel.boundary.plot(ax=ax, color="#222222", alpha=0.4)

axes_in = []

x_dodge = 0.3
y_dodge = 0.1
inset_size = 0.1
for row in df_ca_sel.itertuples():
    if Ara_shortnames_dict[row.ARA_Name] in blacklist:
        continue
#     pop_size = df_pop.loc[row.ARA_Name].EINWOHNER
    pop_size = df_pop[df_pop.ARANR == row.ARA_Nr].EINWOHNER.values[0]
    inset_size_scaled = (inset_size * pop_size / df_pop["EINWOHNER"].max()) ** (1 / 4)

    x_pos = row.geometry.centroid.x + offsets[row.ARA_Name][0]
    y_pos = row.geometry.centroid.y + offsets[row.ARA_Name][1]

    # variant fraction pie charts
    ax_in = ax.inset_axes(
        [
            x_pos - inset_size_scaled / 2 + x_dodge,
            y_pos - inset_size_scaled / 2,
            inset_size_scaled,
            inset_size_scaled,
        ],
        transform=ax.transData,
    )
    df_fractions.loc[Ara_shortnames_dict[row.ARA_Name]].plot(
        ax=ax_in,
        kind="pie",
        y="fraction",
        labels=None,
        legend=False,
        colors=[color_map[variant] for variant in df_fractions.loc[Ara_shortnames_dict[row.ARA_Name]].index],
    )

    ax_in.set_title(
        f"{Ara_shortnames_dict_english[Ara_shortnames_dict[row.ARA_Name]]}\nPop. {round(pop_size/1000)}K",
        fontsize=12,
        pad=-2,
        y=1.000001,
        path_effects=[PathEffects.withStroke(linewidth=5, foreground="w")],
    )

    ax_in.axis("off")
    ax_in.set_aspect("equal")
    
    axes_in.append(ax_in)
   

#  variant legend
variants_presence = df_fractions.reset_index().groupby(["variant"])['fraction'].agg('max')

# minimum presence of variant to be addded to the legend
min_pres = 0.001
variants_presence = variants_presence.loc[lambda x : x > min_pres]
color_map = {key: color_map[key] for key in variants_presence.index}

#### Create sorting list to sort legend labels according to mean frequency
# Reset index if 'variant' and 'ARA_Name' are in the index
df_avg = df_fractions.reset_index()
# Group by variant, average the fractions
variant_avg = df_avg.groupby('variant')['fraction'].mean()
# Sort the variants by average fraction
sorted_variants = variant_avg.sort_values(ascending=False).index.tolist()
filtered_sorted_variants = [v for v in sorted_variants if v in color_map]


ax.legend(
    handles=[
        Patch(facecolor=color_map[variant], edgecolor=color_map[variant], label=variant)
        for variant in filtered_sorted_variants if variant in color_map
    ],
    bbox_to_anchor=(1.04, .7),
    loc="upper left",
    title="Variant",
    title_fontsize=12,
    fontsize=11,
    frameon=False,
)

# finalize axis
ax.axis("off")

# save plot
fig.tight_layout()
#fig.savefig("FOPH_figures/SwissMap_{}.pdf".format(file_out_name))
#fig.savefig("plots/SwissMap_{}.png".format(file_out_name))
#fig.savefig("plots/SwissMap_{}.svg".format(file_out_name))

# Save figures with correct path
fig.savefig(os.path.join(plots_dir, f"SwissMap_{file_out_name}.png"))
fig.savefig(os.path.join(plots_dir, f"SwissMap_{file_out_name}.svg"))

fig.savefig(os.path.join(plots_dir, f"SwissMap_{file_out_name}.pdf"))