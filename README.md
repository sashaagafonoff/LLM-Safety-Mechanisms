# LLM Safety Mechanisms Dataset

A comprehensive, structured dataset tracking safety mechanisms implemented by major LLM providers.

## 🎯 Purpose

This dataset provides researchers, policymakers, and practitioners with:
- Standardized taxonomy of LLM safety techniques
- Evidence-based tracking of implementation across providers
- Verifiable sources for all safety claims
- Machine-readable format for analysis

## 📊 Dataset Structure

The dataset uses a normalized structure with six linked entities:
- **Providers**: LLM companies and organizations
- **Models**: Specific model versions and their capabilities
- **Categories**: Safety mechanism categories (e.g., "Pre-training Safety")
- **Techniques**: Specific safety methods (e.g., "Training Data Filtering")
- **Evidence**: Provider-specific implementations with sources
- **Risk Areas**: Standardized risk taxonomy

## 🚀 Quick Start

```bash
# Validate the dataset
python scripts/validate_data.py

# View evidence for a specific provider
jq '.[] | select(.providerId=="openai")' data/evidence.json

# Generate summary report
python scripts/generate_report.py