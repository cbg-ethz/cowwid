# Automatic Variant Monitoring System

## Overview

Historically we have cared predominantly about clades. New lineages are first noted in Pango-Designations, while Nextstrain nomenclature focuses on major evolutionary branches compared to Pango-Designations. Nextstrain has well-structured data and processes for designation and dataset release.

## System Architecture

### Goals
1. **Trigger Alerts** to CBG / NEXUS once clades are assigned in Nextstrain
2. **Generate Automatic Variant Definitions** for Cowwid from CovSpectrum
3. **Streamline Workflow** from detection to implementation

### Technical Design

The system consists of three interconnected GitHub Actions workflows:

#### 1. **voc-monitor.yaml** - Clade Detection & Alerting
- **Schedule**: Daily at 08:00 UTC
- **Function**: Monitors nextstrain/ncov clade designations for changes
- **Actions**: 
  - Downloads and compares current vs previous clade hierarchy
  - Creates enriched GitHub issues for new clades detected
  - Includes clade display names (e.g., "25C (XFG)") and emergence dates
  - Auto-assigns to @gordonkoehn
  - Adds `variant-creation-needed` label to trigger automation
  - Provides CovSpectrum links for immediate checking

#### 2. **variant-creator.yaml** - Automated Definition Generation
- **Triggers**: 
  - Issues with `variant-creation-needed` label (automatic)
  - Manual workflow dispatch (manual override)
  - Push events (temporary, for testing)
- **Function**: Creates variant definition files from CovSpectrum data
- **Process**:
  1. Queries CovSpectrum API for nucleotide mutations
  2. Applies filtering (minProportion=0.8, minCount=15)
  3. Generates YAML files with `_bot` suffix for automation tracking
  4. Creates clean PRs from master branch with only variant file changes
  5. Links PRs to originating issues via "Closes #X"
- **Safety**: Never modifies master directly, only creates variant branches

#### 3. **variant-retry.yaml** - Failure Recovery
- **Schedule**: Every 4 hours
- **Function**: Retries failed variant creation attempts
- **Logic**: 
  - Finds open issues with `variant-creation-needed` label
  - Retries for up to 48 hours (typical CovSpectrum delay: 16-48h)
  - Handles cases where Nextstrain dataset releases lag behind clade assignment

### Data Flow

```
Nextstrain Clade Assignment
    ↓
voc-monitor (daily 08:00)
    ↓
GitHub Issue Created (with CovSpectrum links)
    ↓ (automatic trigger)
variant-creator (immediate)
    ↓
CovSpectrum API Query
    ↓ (if successful)
PR Creation → Manual Review → Merge
    ↓ (if failed)
variant-retry (every 4h for 48h)
```

### Key Features

- **Automatic Processing**: Handles multiple simultaneous clade detections
- **Error Resilience**: Comprehensive retry mechanism with detailed logging
- **Clean Integration**: PRs contain only variant definition changes
- **Transparency**: Full traceability from detection to implementation
- **Manual Override**: Support for manual processing when needed
- **CovSpectrum Integration**: Direct links for verification and monitoring

### File Naming Convention

- **Manual files**: `variant_mutations_full.yaml`
- **Automated files**: `variant_mutations_full_bot.yaml`

This distinction allows easy identification of automation-generated vs manually curated definitions.

## Implemented Github Actions in Cowwid Repo

- **voc-monitor**: Checks daily 08:00 for changes to nextstrain/ncov clade designations, if new detected, opens an issue in cowwid repo, notifies CBG and NEXUS
- **variant-retry**: Checks every 4 hours if issues in the cowwid repo for new variant designations exist that are not older than 2 days, if so retries variant-creator. May fail initially as nextstrain dataset first has to make a release, hence retry for 2 days.
- **variant-creator**: Creates variant definition by querying CovSpectrum API (like CoJac sig-generate), gets all mutations above a certain frequency threshold and minimum number of sequences filters for that clade

## Contact

System maintained by @gordonkoehn