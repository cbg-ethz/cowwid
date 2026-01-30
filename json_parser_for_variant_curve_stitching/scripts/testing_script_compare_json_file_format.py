# to run the script : conda activate deepdiff-env
from deepdiff import DeepDiff
import json
import pprint

control_file="/cluster/project/pangolin/processes/sars_cov_2/explore-new-variants/variants/results_ba32_202511_202512/deconvoluted_upload.json"
test_file="/cluster/project/pangolin/resources/cowwid/json_parser_for_variant_curve_stitching/results/stitched_curve.json"

with open(control_file) as f1, open(test_file) as f2:
    d1 = json.load(f1)
    d2 = json.load(f2)

def same_date(x, y, level=None):
    if isinstance(x, dict) and isinstance(y, dict):
        return x.get("date") == y.get("date")
    return x == y

def count_timeseries(data):
    counts = {}
    for location, variants in data.items():
        for variant, variant_data in variants.items():
            ts = variant_data.get("timeseriesSummary", [])
            counts[(location, variant)] = len(ts)
    return counts

def dateset(ts):
    return {row.get("date") for row in ts if isinstance(row, dict) and row.get("date")}

def check_date_alignment(data):
    """
    For each location, checks whether all variants have identical date sets in timeseriesSummary.
    Prints only locations with mismatches, showing missing/extra dates per variant.
    """
    problems = []

    for location, variants in data.items():
        if not isinstance(variants, dict) or not variants:
            continue

        per_variant_dates = {}
        for variant, vdata in variants.items():
            ts = (vdata or {}).get("timeseriesSummary", [])
            per_variant_dates[variant] = dateset(ts)

        # reference = variant with the largest date set (most informative)
        ref_variant = max(per_variant_dates, key=lambda v: len(per_variant_dates[v]))
        ref_dates = per_variant_dates[ref_variant]

        mismatching = []
        for variant, dset in per_variant_dates.items():
            if dset != ref_dates:
                missing = sorted(ref_dates - dset)
                extra = sorted(dset - ref_dates)
                mismatching.append((variant, len(dset), len(missing), len(extra), missing[:5], extra[:5]))

        if mismatching:
            problems.append((location, ref_variant, len(ref_dates), mismatching))

    return problems

# ignore_order=True helps if list items are same but in different order
diff = DeepDiff(d1, d2, ignore_order=True, significant_digits=1)
print("-------------------------")
print("Diff CHECK 1:")
pprint.pprint(diff)

diff = DeepDiff(
    d1, d2,
    ignore_order=True,
    significant_digits=1,
    iterable_compare_func=same_date,
    exclude_regex_paths=r".*"
)
print("-------------------------")
print("Diff CHECK 2:")
pprint.pprint(diff)

c1 = count_timeseries(d1)
c2 = count_timeseries(d2)
all_pairs = sorted(set(c1.keys()) | set(c2.keys()))

print("-------------------------")
print("Diff CHECK 3: (no output below is good sign)")
# only print mismatches
for location, variant in all_pairs:
    n1 = c1.get((location, variant), 0)
    n2 = c2.get((location, variant), 0)
    if n1 != n2:
        print(f"{location} | {variant}: control={n1}, test={n2}")

print("-------------------------")
print("DATE GRID CHECK (within each file):")
print("Control file (d1):")
problems1 = check_date_alignment(d1)
if not problems1:
    print("  All locations: all variants share identical date sets.")
else:
    for location, ref_variant, ref_n, mismatching in problems1:
        print(f"\n  {location} (ref={ref_variant}, n_dates={ref_n})")
        for variant, n, n_missing, n_extra, missing5, extra5 in mismatching:
            print(f"    - {variant}: n_dates={n}, missing={n_missing}, extra={n_extra}")
            if n_missing:
                print(f"        missing (first 5): {missing5}")
            if n_extra:
                print(f"        extra   (first 5): {extra5}")

print("\nTest file (d2):")
problems2 = check_date_alignment(d2)
if not problems2:
    print("  All locations: all variants share identical date sets.")
else:
    for location, ref_variant, ref_n, mismatching in problems2:
        print(f"\n  {location} (ref={ref_variant}, n_dates={ref_n})")
        for variant, n, n_missing, n_extra, missing5, extra5 in mismatching:
            print(f"    - {variant}: n_dates={n}, missing={n_missing}, extra={n_extra}")
            if n_missing:
                print(f"        missing (first 5): {missing5}")
            if n_extra:
                print(f"        extra   (first 5): {extra5}")
