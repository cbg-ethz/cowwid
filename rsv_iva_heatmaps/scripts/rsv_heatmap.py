import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import argparse
import sys

# Define a dictionary to map sample ID prefixes to location names
LOCATION_MAP = {
    '05_2025': 'lugano',
    '10_2025': 'zurich',
    '15_2025': 'basel',
    '16_2025': 'geneva',
    '17_2025': 'chur',
    '25_2025': 'laupen'
}

def create_coverage_plot(grouped_data, location_name, output_dir, batch, subtype):
    """
    Creates and saves a multi-subplot figure for log coverage profiles.
    
    Args:
        grouped_data (pd.core.groupby.generic.DataFrameGroupBy): Grouped DataFrame for the location.
        location_name (str): The name of the location (e.g., 'zurich').
        output_dir (str): Base path to save the plots.
        batch (str): Main batch identifier for folder structure.
        subtype (str): Viral subtype (e.g., 'B').
    """
    num_samples = len(grouped_data)
    if num_samples == 0:
        print(f"No samples found for {location_name}. Skipping plot generation.")
        return

    # Use a maximum of 6 rows, or the actual number of samples if less
    num_rows = min(6, num_samples) 
    
    # Calculate the number of subplots needed and adjust figure size dynamically
    # Use ceil to ensure enough rows if num_samples > num_rows
    # Since num_cols is 1, num_rows will be the same as num_samples if num_samples <= 6
    if num_samples > 6:
        # If there are more than 6 samples, create 2 columns and dynamically calculate rows
        num_cols = 2
        num_rows = int(np.ceil(num_samples / num_cols))
        figsize = (15 * num_cols, 4 * num_rows) # Adjust size for 2 columns
    else:
        num_cols = 1
        figsize = (20, 3 * num_samples) # Adjust height based on number of samples for 1 column

    print(f"Plotting {num_samples} samples for {location_name} in a {num_rows}x{num_cols} grid.")
    
    # Create a figure with subplots
    fig, axes = plt.subplots(nrows=num_rows, ncols=num_cols, figsize=figsize)
    axes = axes.flatten()

    # Create a plot for each sample in a subplot
    for i, (sample_name, group) in enumerate(grouped_data):
        ax = axes[i]
        
        ax.plot(group['pos'], group['log_coverage'], linestyle='-', linewidth=0.5)
        ax.fill_between(group['pos'], group['log_coverage'], color='lightblue', alpha=0.5)

        ax.set_title(f'{sample_name}', fontsize=16, fontweight='bold')
        ax.set_xlabel('Position', fontsize=12, fontweight='bold')
        ax.set_ylabel('Log Coverage', fontsize=12, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.tick_params(axis='both', which='major', labelsize=10, width=1.5, length=5)

        # Set thicker axes spines
        for spine in ax.spines.values():
            spine.set_linewidth(1.5)

    # Turn off any unused subplots (if more axes were created than samples)
    for ax in axes[num_samples:]:
        ax.axis('off')

    # Adjust layout to prevent overlap
    plt.tight_layout()

    # Define the output path and filename
    # NOTE: The original script used relative paths '../../plots/all_data/{batch}/...'. 
    # This script creates the folder structure inside the provided output_dir.
    save_dir = os.path.join(output_dir, batch)
    os.makedirs(save_dir, exist_ok=True)
    
    filename = f"rsv_{subtype}_log_coverage_plots_{location_name}_{batch}.png"
    save_path = os.path.join(save_dir, filename)
    
    # Save the figure
    plt.savefig(save_path, dpi=300)
    plt.close(fig)  # Close the figure to free memory
    print(f"Plot saved to: {save_path}")

def main():
    """Main function to parse arguments, process data, and generate plots."""
    
    parser = argparse.ArgumentParser(description="Generate log coverage plots from a collected coverage TSV file.")
    parser.add_argument("-i", "--input_file", required=True, help="Path to the input TSV file (e.g., collected_rsv_coverage_...tsv)")
    parser.add_argument("-o", "--output_dir", required=True, help="Base output directory to save plots (e.g., /path/to/plots/)")
    parser.add_argument("--batch", required=True, help="Main batch identifier for output folder (e.g., 20250307_2418653583)")
    parser.add_argument("--subtype", required=True, help="Viral subtype (e.g., B)")

    args = parser.parse_args()

    # --- 1. Load and Prepare Data ---
    
    try:
        df = pd.read_csv(args.input_file, sep='\t')
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    print(f"Successfully loaded data from {args.input_file}. Total rows: {len(df)}")
    
    # Calculate log coverage and replace -inf (from log10(0)) with 0
    df['log_coverage'] = np.log10(df['coverage']).replace(-np.inf, 0)
    df = df.drop(columns='coverage', errors='ignore')

    # --- 2. Filter, Group, and Plot ---
    
    all_locations = {}
    
    # Filter the DataFrame for each location based on the suffix patterns in the sample name
    for pattern, location_name in LOCATION_MAP.items():
        # The pattern is '_ID_YEAR_' (e.g., '_05_2025_')
        
        # NOTE: Your original filtering was based on the internal sample ID pattern: 
        # df[df['sample'].str.contains('_05_2025_')]
        # This implementation uses that logic to filter.
        
        location_df = df[df['sample'].str.contains(f'_{pattern}_', na=False, regex=False)]
        
        if not location_df.empty:
            all_locations[location_name] = location_df.groupby('sample')
    
    # Create plots for each grouped location
    if all_locations:
        for location_name, grouped_data in all_locations.items():
            create_coverage_plot(
                grouped_data, 
                location_name, 
                args.output_dir, 
                args.batch, 
                args.subtype
            )
    else:
        print("Warning: No samples were found matching the expected location patterns in the input file.")

if __name__ == "__main__":
    main()