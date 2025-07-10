#!/bin/bash

# GitHub CLI commands to create issues
# Run: gh auth login (if not authenticated)
# Then: bash create_issues.sh

echo 'Creating issue 1/5...'
gh issue create --title "[Evidence Needed] OpenAI - Multiple Techniques" --body "## Provider: OpenAI

We need evidence for the following safety techniques:

- [ ] CSAM Detection & Removal
- [ ] Reinforcement Learning from Human Feedback
- [ ] CSAM Detection & Removal
- [ ] Reinforcement Learning from Human Feedback
- [ ] Copyright Content Filtering
- [ ] Bias Detection in Training Data
- [ ] PII Reduction
- [ ] Constitutional AI / Self-Critique
- [ ] Safety Reward Modeling
- [ ] Input Content Classification

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `openai`
" --label "evidence,help wanted"
sleep 2  # Rate limiting

echo 'Creating issue 2/5...'
gh issue create --title "[Evidence Needed] Anthropic - Multiple Techniques" --body "## Provider: Anthropic

We need evidence for the following safety techniques:

- [ ] CSAM Detection & Removal
- [ ] CSAM Detection & Removal
- [ ] Copyright Content Filtering
- [ ] Bias Detection in Training Data
- [ ] PII Reduction
- [ ] Safety Reward Modeling
- [ ] Input Content Classification
- [ ] Output Content Filtering
- [ ] Prompt Injection Protection
- [ ] Capability Threshold Monitoring

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `anthropic`
" --label "evidence,help wanted"
sleep 2  # Rate limiting

echo 'Creating issue 3/5...'
gh issue create --title "[Evidence Needed] Google - Multiple Techniques" --body "## Provider: Google

We need evidence for the following safety techniques:

- [ ] CSAM Detection & Removal
- [ ] CSAM Detection & Removal
- [ ] Copyright Content Filtering
- [ ] Bias Detection in Training Data
- [ ] PII Reduction
- [ ] Constitutional AI / Self-Critique
- [ ] Safety Reward Modeling
- [ ] Input Content Classification
- [ ] Output Content Filtering
- [ ] Prompt Injection Protection

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `google`
" --label "evidence,help wanted"
sleep 2  # Rate limiting

echo 'Creating issue 4/5...'
gh issue create --title "[Evidence Needed] Meta - Multiple Techniques" --body "## Provider: Meta

We need evidence for the following safety techniques:

- [ ] CSAM Detection & Removal
- [ ] CSAM Detection & Removal
- [ ] Copyright Content Filtering
- [ ] Bias Detection in Training Data
- [ ] PII Reduction
- [ ] Constitutional AI / Self-Critique
- [ ] Safety Reward Modeling
- [ ] Output Content Filtering
- [ ] Prompt Injection Protection
- [ ] Red Team Exercises

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `meta`
" --label "evidence,help wanted"
sleep 2  # Rate limiting

echo 'Creating issue 5/5...'
gh issue create --title "[Evidence Needed] Amazon - Multiple Techniques" --body "## Provider: Amazon

We need evidence for the following safety techniques:

- [ ] Training Data Filtering
- [ ] CSAM Detection & Removal
- [ ] Reinforcement Learning from Human Feedback
- [ ] CSAM Detection & Removal
- [ ] Reinforcement Learning from Human Feedback
- [ ] Copyright Content Filtering
- [ ] Bias Detection in Training Data
- [ ] Constitutional AI / Self-Critique
- [ ] Safety Reward Modeling
- [ ] Prompt Injection Protection

## How to Contribute

1. Check the provider's official documentation:
   - System/Model cards
   - Safety documentation
   - Research papers
   - API documentation

2. For each technique found:
   - Fork the repository
   - Run `python scripts/extract_evidence.py` to get a template
   - Fill in the evidence with sources
   - Submit a PR

## Priority Techniques
Focus on these first:
- CSAM Detection & Removal
- Bias Detection in Training Data
- PII Reduction
- Prompt Injection Protection

Label: `evidence`, `help wanted`, `amazon`
" --label "evidence,help wanted"
sleep 2  # Rate limiting

