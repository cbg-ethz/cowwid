#!/usr/bin/env Rscript

# Load necessary libraries
suppressPackageStartupMessages({
  library(data.table)
  library(tidyverse)
  library(ggplot2)
  library(gridExtra)
  library(optparse)
})

# ... (Configuration and Argument Parsing remain the same) ...
option_list = list(
  make_option(c("-i", "--input_files"), type="character", default=NULL, 
              help="Comma-separated list of input mutation TSV files (e.g., H1_Mutations.tsv,N1_Mutations.tsv)", 
              metavar="file"),
  make_option(c("-o", "--output_path"), type="character", default="./plots/", 
              help="Output directory for saving plots [default: %default]", 
              metavar="directory"),
  make_option(c("-r", "--resistance_file"), type="character", 
              default="/Users/kkirschen/Projects/temp/Influenza/N1_resistanceMuts.tsv", 
              help="Path to the resistance mutations TSV file [default: %default]", 
              metavar="file")
)

opt_parser = OptionParser(option_list=option_list)
opt = parse_args(opt_parser)

if (is.null(opt$input_files)){
  print_help(opt_parser)
  stop("At least one input file must be supplied (e.g., -i H1_Mutations.tsv,N1_Mutations.tsv)", call.=FALSE)
}

# Split input file string into a vector of file paths
input_files <- unlist(strsplit(opt$input_files, ","))
output_dir <- opt$output_path
resistance_file <- opt$resistance_file

# Create output directory if it doesn't exist
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Load resistance mutations (This file is assumed to exist)
if (file.exists(resistance_file)) {
  N1_resistance_mut <- fread(resistance_file)$AA_mutations
} else {
  warning(paste("Resistance file not found at:", resistance_file, "Resistance filtering will be skipped for all files."))
  N1_resistance_mut <- character(0) # Empty vector
}

# --- Plotting Function ---
plotting <- function(dt, gene_name, monitore_resitance = FALSE, resistance_muts = character(0)){
  
  # ### NEW CHECK: Check if data is already empty before pre-processing
  if (nrow(dt) == 0) {
      message(paste("Data for", gene_name, "(pre-filter) is empty. Skipping plot generation."))
      return(NULL)
  }

  # Data Pre-processing
  dt$date <- as.factor(dt$date)
  dt$location_short = str_extract(dt$location,"\\(.+\\)")
  dt$location_short = gsub("\\(|\\)","",dt$location_short)
  
  if (monitore_resitance && length(resistance_muts) > 0) {
    dt <- dt %>% filter(mut_lable %in% resistance_muts)
    if (nrow(dt) == 0) {
      message(paste("No resistance mutations found for", gene_name, "in the input data. Skipping plot generation."))
      return(NULL)
    }
  }
  
  # ### NEW CHECK: Check if data is empty after filtering (for resistance plots)
  if (nrow(dt) == 0) {
      message(paste("Data for", gene_name, "(post-filter) is empty. Skipping plot generation."))
      return(NULL)
  }
  
  # --- ggplot functions (AA, Nuc, Coverage) ---
  
  # 1. Amino Acid (AA) Mutation Frequency Heatmap
  p_AA <- ggplot(dt, aes(x = as.factor(gene_codonIDX), y = as.factor(date), fill = AF)) +
    geom_tile() +
    facet_grid(vars(location_short), switch = "y", scales = "free") +
    scale_fill_gradient(low = "lightblue", high = "darkblue", na.value = NA) +
    theme_light() +
    scale_x_discrete(breaks=dt$gene_codonIDX, labels=dt$mut_lable) +
    labs(title = paste(gene_name, "Amino Acid Mutation Frequency"), fill = "Mutation Frequency") +
    theme(axis.title.x = element_blank(), 
          axis.title.y = element_blank(), 
          axis.text.x = element_text(angle = 90, hjust = 1, size = 10),
          strip.text = element_text(size = 10))
  
  # 2. Nucleotide (Nuc) Mutation Frequency Heatmap
  p_nuc <- p_AA + scale_x_discrete(breaks=dt$gene_codonIDX, labels=dt$mut_lable_nuc) + 
    labs(title = paste(gene_name, "Nucleotide Mutation Frequency"))

  # 3. Coverage (DP) Heatmap
  p_cov <- ggplot(dt, aes(x = as.factor(gene_codonIDX), y = as.factor(date), fill = DP)) +
    geom_tile() +
    facet_grid(vars(location_short), switch = "y", scales = "free") +
    scale_fill_gradient(low = "lightblue", high = "darkblue", na.value = NA, trans = "log") +
    theme_light() +
    scale_x_discrete(breaks=dt$gene_codonIDX, labels=dt$mut_lable) +
    labs(title = paste(gene_name, "Coverage (log scale)"), fill = "Read Depth (DP)") +
    theme(axis.title.x = element_blank(), 
          axis.title.y = element_blank(), 
          axis.text.x = element_text(angle = 90, hjust = 1, size = 10),
          strip.text = element_text(size = 10))
  
  # Create a combined plot (AA and Coverage)
  # NOTE: grid.arrange will still fail if p_AA or p_cov failed to build, but 
  # our prior checks should prevent that.
  p_combined <- grid.arrange(p_AA, p_cov, ncol = 1)
  
  return(list(hm_nuc = p_nuc, hm_aa = p_AA, hm_cov = p_cov, p_combined = p_combined, det_res = dt))
}

# --- Main Processing Loop ---
for (file_path in input_files) {
  if (!file.exists(file_path)) {
    warning(paste("File not found:", file_path, "Skipping."))
    next
  }
  
  message(paste("Processing file:", file_path))
  
  # Derive gene name from file name (e.g., H1_Mutations.tsv -> H1)
  gene_name <- tools::file_path_sans_ext(basename(file_path))
  
  # Read the data
  dt <- fread(file_path)
  
  # ### NEW CHECK: Early return if data read is empty
  if (nrow(dt) == 0) {
      message(paste("Input file", file_path, "is empty. Skipping."))
      next
  }

  # 1. Standard Plots
  plots_standard <- plotting(dt, gene_name)
  
  # ... (Saving logic for standard plots remains the same, relies on !is.null) ...
  if (!is.null(plots_standard)) {
    # Save standard plots
    ggsave(filename = file.path(output_dir, paste0(gene_name, "_AA_Mutation_Freq.pdf")), 
           plot = plots_standard$hm_aa, width = 10, height = 7)
    ggsave(filename = file.path(output_dir, paste0(gene_name, "_Nuc_Mutation_Freq.pdf")), 
           plot = plots_standard$hm_nuc, width = 10, height = 7)
    ggsave(filename = file.path(output_dir, paste0(gene_name, "_Coverage.pdf")), 
           plot = plots_standard$hm_cov, width = 10, height = 7)
    # Save combined plot
    ggsave(filename = file.path(output_dir, paste0(gene_name, "_Combined.pdf")), 
           plot = plots_standard$p_combined, width = 10, height = 10, device = "pdf")
  }

  # 2. Resistance Plots (Only if resistance mutations are defined and the gene is N1)
  if (gene_name == "N1_Mutations" || gene_name == "N1") {
    
    plots_res <- plotting(dt, gene_name = "N1_Resistance", monitore_resitance = TRUE, resistance_muts = N1_resistance_mut)
    
    if (!is.null(plots_res)) {
      # Save resistance plots
      ggsave(filename = file.path(output_dir, "N1_Resistance_AA_Mutation_Freq.pdf"), 
             plot = plots_res$hm_aa, width = 10, height = 7)
      ggsave(filename = file.path(output_dir, "N1_Resistance_Coverage.pdf"), 
             plot = plots_res$hm_cov, width = 10, height = 7)
      
      # Save the detailed data table for detected resistance mutations
      fwrite(plots_res$det_res, file.path(output_dir, "N1_Detected_Resistance_Mutations.tsv"), sep = "\t")
    }
  }
}
dev.off()
message("Processing complete. Plots and data saved to:", output_dir)