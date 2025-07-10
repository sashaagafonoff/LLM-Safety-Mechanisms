import os
import json
import requests
from pathlib import Path
import PyPDF2
import openai
from datetime import datetime

class LLMEvidenceExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        # Load our schema
        with open('data/techniques.json', 'r') as f:
            self.techniques = json.load(f)
        
        with open('data/providers.json', 'r') as f:
            self.providers = {p['id']: p for p in json.load(f)}
    
    def download_content(self, url):
        """Download and extract text from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                if url.endswith('.pdf'):
                    # Extract PDF text
                    import io
                    pdf_file = io.BytesIO(response.content)
                    reader = PyPDF2.PdfReader(pdf_file)
                    text = ""
                    for page in reader.pages[:20]:  # First 20 pages
                        text += page.extract_text()
                    return text
                else:
                    return response.text[:50000]  # First 50k chars
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None
    
    def extract_safety_evidence(self, content, provider_id, source_url):
        """Use GPT-4 to extract safety evidence from content"""
        
        # Prepare technique list for the prompt
        technique_list = "\n".join([
            f"- {t['id']}: {t['name']} - {t['description']}"
            for t in self.techniques[:10]  # Top techniques
        ])
        
        prompt = f"""You are an AI safety researcher analyzing documentation for safety mechanisms.

Provider: {self.providers[provider_id]['name']}
Source URL: {source_url}

Known safety techniques to look for:
{technique_list}

Content to analyze:
{content[:8000]}

For each safety technique you find evidence of, extract:
1. Technique ID (from the list above)
2. Implementation summary (2-3 sentences)
3. Specific quote or section reference
4. Implementation date (if mentioned)
5. Rating: high (detailed with metrics), medium (documented), low (mentioned briefly)

Format as JSON array:
[
  {{
    "techniqueId": "tech-xxx",
    "summary": "...",
    "quote": "...",
    "section": "...",
    "implementationDate": "YYYY-MM-DD or null",
    "rating": "high|medium|low",
    "confidence": 0.0-1.0
  }}
]

Only include techniques with clear evidence. Be conservative - when in doubt, don't include."""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a precise AI safety documentation analyst. Only extract claims that are explicitly stated."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                evidence_list = json.loads(json_match.group())
                return evidence_list
            
        except Exception as e:
            print(f"LLM extraction error: {e}")
        
        return []
    
    def create_evidence_records(self, extracted_evidence, provider_id, source_url, source_type):
        """Convert extracted evidence to our schema format"""
        
        evidence_records = []
        
        for item in extracted_evidence:
            if item['confidence'] < 0.7:  # Skip low confidence
                continue
            
            # Generate unique ID
            technique_id = item['techniqueId']
            evidence_id = f"ev-auto-{provider_id}-{technique_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            record = {
                "id": evidence_id,
                "providerId": provider_id,
                "techniqueId": technique_id,
                "modelIds": [],  # Will be filled by model detector
                "rating": item['rating'],
                "severityBand": "C",  # Claimed until human verified
                "ratingCriteria": {
                    "publiclyDocumented": True,
                    "independentlyVerified": False,
                    "quantitativeMetrics": "metrics" in item.get('quote', '').lower(),
                    "automatedTest": False
                },
                "summary": item['summary'],
                "evidenceLevel": "primary" if source_type in ['blog', 'documentation'] else "secondary",
                "sourceUrls": [{
                    "url": source_url,
                    "documentType": source_type,
                    "lastVerified": datetime.now().strftime('%Y-%m-%d'),
                    "sourceHash": "0" * 64,  # Will be updated by verifier
                    "relevantSection": item.get('section', item.get('quote', '')[:50] + '...')
                }],
                "implementationDate": item.get('implementationDate'),
                "lastReviewed": datetime.now().strftime('%Y-%m-%d'),
                "reviewFrequency": "P3M",
                "reviewer": "llm-extractor",
                "evaluationMetrics": [],
                "knownLimitations": [],
                "deploymentScope": "all-users",
                "geographicRestrictions": [],
                "complianceStandards": [],
                "notes": f"Auto-extracted with {item['confidence']:.0%} confidence"
            }
            
            evidence_records.append(record)
        
        return evidence_records
    
    def process_new_source(self, source_info):
        """Process a single new source"""
        print(f"\n📄 Processing: {source_info['title']}")
        
        # Download content
        content = self.download_content(source_info['url'])
        if not content:
            return []
        
        # Extract evidence
        extracted = self.extract_safety_evidence(
            content, 
            source_info['provider'],
            source_info['url']
        )
        
        if not extracted:
            print("  No evidence found")
            return []
        
        # Create records
        records = self.create_evidence_records(
            extracted,
            source_info['provider'],
            source_info['url'],
            source_info['type']
        )
        
        print(f"  ✅ Found {len(records)} evidence items")
        return records

def run_automated_extraction():
    """Main automation pipeline"""
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("❌ Need OPENAI_API_KEY environment variable")
        return
    
    extractor = LLMEvidenceExtractor()
    
    # Get new sources
    from source_monitor import monitor_all_sources
    new_sources = monitor_all_sources()
    
    if not new_sources:
        print("No new sources found")
        return
    
    # Process each source
    all_new_evidence = []
    for source in new_sources:
        evidence = extractor.process_new_source(source)
        all_new_evidence.extend(evidence)
    
    if all_new_evidence:
        # Load existing evidence
        with open('data/evidence.json', 'r') as f:
            existing = json.load(f)
        
        # Add new evidence
        existing.extend(all_new_evidence)
        
        # Save
        with open('data/evidence.json', 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"\n✅ Added {len(all_new_evidence)} new evidence records!")
        
        # Create automated PR
        branch_name = f"auto-evidence-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        os.system(f"git checkout -b {branch_name}")
        os.system("git add data/evidence.json")
        os.system(f'git commit -m "chore: auto-extracted {len(all_new_evidence)} evidence records"')
        print(f"\n📌 Created branch: {branch_name}")
        print("Review and push when ready")

if __name__ == "__main__":
    run_automated_extraction()