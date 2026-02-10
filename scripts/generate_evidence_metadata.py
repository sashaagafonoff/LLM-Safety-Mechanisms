"""
One-time script to generate and append content_metadata to evidence.json.

Usage:
    python scripts/generate_evidence_metadata.py [--test] [--id <doc_id>]

    --test: Dry run mode, shows what would be added without modifying evidence.json
    --id: Process only a specific document ID
"""

import json
import os
import sys
from pathlib import Path
import argparse
from typing import Dict, Optional

# Try to import anthropic, but allow test mode without it
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

# Configuration
EVIDENCE_PATH = Path("data/evidence.json")
FLAT_TEXT_DIR = Path("data/flat_text")
API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Metadata generation prompt template
METADATA_PROMPT = """Analyze this AI safety documentation and provide structured metadata.

SOURCE_ID: {doc_id}
DOCUMENT_TYPE: {doc_type}
PROVIDER: {provider}
TITLE: {title}

CONTENT (first 4000 characters):
{content_preview}

Provide JSON with these fields:

1. document_purpose: Choose ONE from [primary_research, system_card, policy, documentation, blog_post, marketing]
   - primary_research: Academic papers, technical reports with novel research
   - system_card: Formal model cards, system cards, safety reports
   - policy: Corporate policies, terms of service, responsible use guides
   - documentation: API docs, developer guides, how-to documentation
   - blog_post: Announcements, updates, informal communications
   - marketing: Product marketing materials

2. signal_strength: Choose ONE from [high, medium, low]
   - high: Authoritative, detailed, official source with specific implementation details
   - medium: Official but high-level, or detailed but unofficial
   - low: Vague, marketing-focused, or minimal technical detail

3. temporal_focus: Choose ONE from [implemented, planned, research, historical, mixed]
   - implemented: Describes what IS deployed/used currently
   - planned: Describes future intentions, roadmap
   - research: Academic research without deployment claims
   - historical: Retrospective analysis
   - mixed: Combination of above

4. scope: Choose ONE from [specific_model, model_family, provider_wide, industry_wide]
   - specific_model: Focuses on a single specific model
   - model_family: Covers a family of models (e.g., GPT-4 series)
   - provider_wide: Describes company-wide practices
   - industry_wide: General discussion of AI safety practices

5. technical_depth: Choose ONE from [deep, moderate, shallow]
   - deep: Detailed technical implementation, algorithms, architectures
   - moderate: Some technical detail but not comprehensive
   - shallow: High-level overview, minimal technical specifics

6. primary_topics: List 2-6 topics from this taxonomy (most relevant first):
   - pre_training_safety (data curation, filtering, CSAM detection)
   - alignment_methods (RLHF, Constitutional AI, DPO, fine-tuning)
   - input_guardrails (input filtering, prompt classification)
   - output_guardrails (output filtering, content moderation)
   - runtime_safety (system prompts, circuit breakers, monitoring)
   - red_teaming (adversarial testing, penetration testing)
   - safety_benchmarking (evaluation metrics, test suites)
   - transparency (model cards, documentation)
   - governance (oversight, advisory boards, compliance)
   - privacy_protection (PII redaction, data retention)
   - security (adversarial defense, access control)
   - ip_protection (copyright, watermarking)

7. excluded_topics: List 2-4 topics that are explicitly NOT covered (from same taxonomy)

8. confidence_weight: Float 0.0-1.0 indicating source reliability
   - 1.0: Official technical report or system card
   - 0.9: Academic paper with strong evidence
   - 0.8: Official documentation with good detail
   - 0.7: Official but high-level or marketing-oriented
   - 0.6: Blog post or unofficial but credible
   - 0.5: Minimal information or unclear sourcing

9. language: Two-letter language code (e.g., "en", "zh")

10. notes: One-sentence description of document's unique contribution or focus

Return ONLY valid JSON with these exact field names. No additional commentary.

Example format:
{{
  "document_purpose": "system_card",
  "signal_strength": "high",
  "temporal_focus": "implemented",
  "scope": "specific_model",
  "technical_depth": "deep",
  "primary_topics": ["alignment_methods", "red_teaming", "safety_benchmarking"],
  "excluded_topics": ["pre_training_safety", "ip_protection"],
  "confidence_weight": 0.95,
  "language": "en",
  "notes": "Comprehensive safety evaluation with detailed red teaming results"
}}
"""


class MetadataGenerator:
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.client = None

        if not test_mode:
            if not ANTHROPIC_AVAILABLE:
                raise ValueError(
                    "anthropic package not installed. Install with: pip install anthropic"
                )
            if not API_KEY:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=API_KEY)

    def load_evidence(self) -> Dict:
        """Load evidence.json"""
        with open(EVIDENCE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_evidence(self, data: Dict):
        """Save evidence.json with formatting"""
        with open(EVIDENCE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_flat_text_path(self, doc_id: str) -> Optional[Path]:
        """Find flat text file for document ID"""
        # Try exact match
        path = FLAT_TEXT_DIR / f"{doc_id}.txt"
        if path.exists():
            return path

        # Try case-insensitive match
        for file in FLAT_TEXT_DIR.glob("*.txt"):
            if file.stem.lower() == doc_id.lower():
                return file

        return None

    def read_flat_text(self, path: Path, max_chars: int = 4000) -> str:
        """Read flat text file, skipping header"""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip header (everything before "----")
        parts = content.split("-" * 20, 1)
        if len(parts) > 1:
            content = parts[1].strip()

        return content[:max_chars]

    def generate_metadata(self, doc_id: str, source: Dict) -> Optional[Dict]:
        """Generate metadata for a single document"""

        # Find flat text file
        flat_path = self.get_flat_text_path(doc_id)
        if not flat_path:
            print(f"  ⚠️  No flat text file found for {doc_id}")
            return None

        # Read content preview
        content_preview = self.read_flat_text(flat_path)

        if self.test_mode:
            print(f"  [TEST MODE] Would generate metadata from {len(content_preview)} chars")
            return {
                "document_purpose": "TEST",
                "signal_strength": "TEST",
                "temporal_focus": "TEST",
                "scope": "TEST",
                "technical_depth": "TEST",
                "primary_topics": ["TEST"],
                "excluded_topics": ["TEST"],
                "confidence_weight": 0.0,
                "language": "en",
                "notes": "TEST MODE - no API call made"
            }

        # Generate prompt
        prompt = METADATA_PROMPT.format(
            doc_id=doc_id,
            doc_type=source.get('type', 'Unknown'),
            provider=source.get('provider', 'Unknown'),
            title=source.get('title', 'Unknown'),
            content_preview=content_preview
        )

        # Call Claude API
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            metadata_json = response.content[0].text.strip()

            # Remove markdown code blocks if present
            if metadata_json.startswith("```"):
                lines = metadata_json.split("\n")
                metadata_json = "\n".join(lines[1:-1])

            metadata = json.loads(metadata_json)

            # Validate required fields
            required_fields = [
                "document_purpose", "signal_strength", "temporal_focus",
                "scope", "technical_depth", "primary_topics",
                "excluded_topics", "confidence_weight", "language", "notes"
            ]

            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"Missing required field: {field}")

            return metadata

        except Exception as e:
            print(f"  ❌ Error generating metadata: {str(e)}")
            return None

    def process_all(self, target_id: Optional[str] = None):
        """Process all documents or a specific one"""

        # Load evidence
        data = self.load_evidence()
        sources = data.get('sources', [])

        print(f"{'='*70}")
        print(f"EVIDENCE METADATA GENERATOR")
        print(f"{'='*70}")
        print(f"Mode: {'TEST (dry run)' if self.test_mode else 'PRODUCTION'}")
        print(f"Total sources: {len(sources)}")
        print()

        # Statistics
        stats = {
            'total': len(sources),
            'processed': 0,
            'added': 0,
            'skipped_existing': 0,
            'skipped_no_file': 0,
            'errors': 0
        }

        for i, source in enumerate(sources, 1):
            doc_id = source.get('id')
            if not doc_id:
                print(f"[{i}/{stats['total']}] ⚠️  Source missing ID, skipping")
                stats['errors'] += 1
                continue

            # Filter by target ID if specified
            if target_id and doc_id.lower() != target_id.lower():
                continue

            print(f"[{i}/{stats['total']}] Processing: {doc_id}")

            # Check if metadata already exists
            if 'content_metadata' in source:
                print(f"  ✓ Metadata already exists, skipping")
                stats['skipped_existing'] += 1
                continue

            # Generate metadata
            metadata = self.generate_metadata(doc_id, source)

            if metadata is None:
                stats['skipped_no_file'] += 1
                continue

            # Add metadata to source
            source['content_metadata'] = metadata
            stats['added'] += 1
            stats['processed'] += 1

            print(f"  ✓ Generated metadata:")
            print(f"    Purpose: {metadata['document_purpose']}")
            print(f"    Signal: {metadata['signal_strength']}")
            print(f"    Focus: {metadata['temporal_focus']}")
            print(f"    Topics: {', '.join(metadata['primary_topics'][:3])}")
            print()

        # Save updated evidence.json
        if not self.test_mode and stats['added'] > 0:
            print(f"{'='*70}")
            print("SAVING CHANGES...")
            self.save_evidence(data)
            print(f"✓ Saved {stats['added']} metadata entries to {EVIDENCE_PATH}")

        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total sources: {stats['total']}")
        print(f"Metadata added: {stats['added']}")
        print(f"Already had metadata: {stats['skipped_existing']}")
        print(f"No flat text file: {stats['skipped_no_file']}")
        print(f"Errors: {stats['errors']}")
        print(f"\nCoverage: {stats['added'] + stats['skipped_existing']}/{stats['total']} " +
              f"({100 * (stats['added'] + stats['skipped_existing']) / stats['total']:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Generate and append content_metadata to evidence.json"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: show what would be done without making API calls or modifying files"
    )
    parser.add_argument(
        "--id",
        type=str,
        help="Process only a specific document ID"
    )

    args = parser.parse_args()

    generator = MetadataGenerator(test_mode=args.test)
    generator.process_all(target_id=args.id)


if __name__ == "__main__":
    main()
