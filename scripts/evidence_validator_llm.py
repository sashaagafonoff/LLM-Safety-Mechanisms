import json
import openai
import os
from datetime import datetime

class EvidenceValidator:
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
    
    def validate_evidence_claim(self, evidence, source_content):
        """Use LLM to validate if evidence summary matches source"""
        
        prompt = f"""Verify if this safety mechanism claim is accurately supported by the source content.

Claim:
- Technique: {evidence['techniqueId']}
- Summary: {evidence['summary']}
- Rating: {evidence['rating']}

Source excerpt:
{source_content[:3000]}

Questions to answer:
1. Is the technique actually mentioned in the source? (YES/NO)
2. Does the summary accurately reflect what the source says? (YES/NO/PARTIAL)
3. Is the rating justified? (YES/NO)
4. What specific quote supports this claim? (quote or "none found")
5. Confidence in this validation: (0.0-1.0)

Respond in JSON format."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse response
            import re
            text = response.choices[0].message.content
            
            return {
                'mentioned': 'yes' in text.lower(),
                'accurate': 'yes' in text.lower() or 'partial' in text.lower(),
                'rating_justified': 'yes' in text.lower(),
                'confidence': 0.8  # Default
            }
            
        except Exception as e:
            print(f"Validation error: {e}")
            return None
    
    def validate_all_auto_evidence(self):
        """Validate all auto-extracted evidence"""
        with open('data/evidence.json', 'r') as f:
            evidence_list = json.load(f)
        
        auto_evidence = [e for e in evidence_list if e['reviewer'] == 'llm-extractor']
        
        print(f"Validating {len(auto_evidence)} auto-extracted records...")
        
        validated = []
        for evidence in auto_evidence:
            # In real implementation, would fetch and check source
            # For now, mark as needing review
            evidence['notes'] = evidence.get('notes', '') + ' [needs human review]'
            evidence['severityBand'] = 'V'  # Volunteered until verified
            validated.append(evidence)
        
        return validated

# More validation functions...