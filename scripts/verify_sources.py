import requests
import hashlib
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import PyPDF2
import io
from urllib.parse import urlparse

class SourceVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (LLM-Safety-Mechanisms/1.0; +https://github.com/sashaagafonoff/LLM-Safety-Mechanisms)'
        })
        self.failed_sources = []
        self.updated_sources = []
        
    def calculate_content_hash(self, content, url):
        """Calculate hash based on content type"""
        if isinstance(content, bytes):
            # For PDFs and binary content
            return hashlib.sha256(content).hexdigest()
        else:
            # For text content, normalize line endings
            normalized = content.replace('\r\n', '\n').replace('\r', '\n')
            return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def extract_pdf_text(self, content):
        """Extract text from PDF for verification"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages[:5]:  # First 5 pages
                text += page.extract_text()
            return text
        except Exception as e:
            print(f"    ⚠️  PDF extraction failed: {e}")
            return ""
    
    def verify_url(self, url, expected_hash=None):
        """Verify URL accessibility and content"""
        try:
            print(f"  🔍 Checking {url[:80]}...")
            
            # Special handling for different domains
            if "arxiv.org" in url and "/abs/" in url:
                # Convert abstract URL to PDF URL
                pdf_url = url.replace("/abs/", "/pdf/") + ".pdf"
                response = self.session.get(pdf_url, timeout=30)
            else:
                response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                content = response.content
                content_type = response.headers.get('Content-Type', '')
                
                # Calculate hash
                new_hash = self.calculate_content_hash(content, url)
                
                # Extract text for verification if PDF
                extracted_text = ""
                if 'pdf' in content_type.lower() or url.endswith('.pdf'):
                    extracted_text = self.extract_pdf_text(content)
                
                result = {
                    'accessible': True,
                    'status_code': 200,
                    'content_hash': new_hash,
                    'hash_changed': expected_hash and expected_hash != new_hash and expected_hash != "0" * 64,
                    'content_type': content_type,
                    'content_length': len(content),
                    'last_modified': response.headers.get('Last-Modified', ''),
                    'extracted_text_preview': extracted_text[:200] if extracted_text else None
                }
                
                if result['hash_changed']:
                    print(f"    ⚠️  Content changed! Old: {expected_hash[:8]}... New: {new_hash[:8]}...")
                else:
                    print(f"    ✅ Verified (hash: {new_hash[:8]}...)")
                
                return result
            else:
                print(f"    ❌ HTTP {response.status_code}")
                return {
                    'accessible': False,
                    'status_code': response.status_code,
                    'error': f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            print(f"    ❌ Timeout")
            return {'accessible': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:50]}")
            return {'accessible': False, 'error': str(e)}
    
    def verify_evidence_content(self, evidence, source, extracted_text):
        """Verify that source actually contains evidence about the technique"""
        technique_keywords = {
            'tech-training-data-filtering': ['filter', 'training data', 'dataset', 'curat'],
            'tech-constitutional-ai': ['constitutional', 'critique', 'harmless', 'helpful', 'honest'],
            'tech-rlhf': ['reinforcement learning', 'human feedback', 'RLHF', 'preference'],
            'tech-red-teaming': ['red team', 'adversarial', 'security test'],
            'tech-safety-documentation': ['safety', 'document', 'transparent', 'card'],
            # Add more as needed
        }
        
        keywords = technique_keywords.get(evidence['techniqueId'], [])
        if not keywords or not extracted_text:
            return True  # Can't verify, assume OK
        
        text_lower = extracted_text.lower()
        found = any(keyword.lower() in text_lower for keyword in keywords)
        
        if not found:
            print(f"    ⚠️  Warning: Couldn't find technique keywords in source")
        
        return found
    
    def verify_all_sources(self, check_new_only=False):
        """Verify all sources in evidence.json"""
        print("🔍 Starting source verification...\n")
        
        with open('data/evidence.json', 'r') as f:
            evidence_list = json.load(f)
        
        total_sources = sum(len(e['sourceUrls']) for e in evidence_list)
        verified_count = 0
        updated_count = 0
        
        for evidence in evidence_list:
            print(f"\n📄 Verifying {evidence['id']} ({evidence['providerId']} - {evidence['techniqueId']})")
            
            for source in evidence['sourceUrls']:
                # Skip if already verified recently (within 7 days)
                if check_new_only and source.get('lastVerified'):
                    last_verified = datetime.strptime(source['lastVerified'], '%Y-%m-%d')
                    if datetime.now() - last_verified < timedelta(days=7):
                        print(f"  ⏭️  Skipping (verified {source['lastVerified']})")
                        continue
                
                # Verify the URL
                result = self.verify_url(source['url'], source.get('sourceHash'))
                verified_count += 1
                
                if result['accessible']:
                    # Update source information
                    old_hash = source.get('sourceHash', '')
                    source['sourceHash'] = result['content_hash']
                    source['lastVerified'] = datetime.now().strftime('%Y-%m-%d')
                    
                    if old_hash != result['content_hash']:
                        updated_count += 1
                        self.updated_sources.append({
                            'evidence_id': evidence['id'],
                            'url': source['url'],
                            'old_hash': old_hash,
                            'new_hash': result['content_hash']
                        })
                    
                    # Verify content relevance if we have extracted text
                    if result.get('extracted_text_preview'):
                        self.verify_evidence_content(evidence, source, result['extracted_text_preview'])
                else:
                    self.failed_sources.append({
                        'evidence_id': evidence['id'],
                        'url': source['url'],
                        'error': result.get('error', 'Unknown error')
                    })
                
                # Rate limiting
                time.sleep(1)
        
        # Save updated evidence
        with open('data/evidence.json', 'w') as f:
            json.dump(evidence_list, f, indent=2)
        
        # Generate verification report
        self.generate_report(total_sources, verified_count, updated_count)
        
        return len(self.failed_sources) == 0
    
    def generate_report(self, total, verified, updated):
        """Generate verification report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_sources': total,
                'verified': verified,
                'updated': updated,
                'failed': len(self.failed_sources)
            },
            'failed_sources': self.failed_sources,
            'updated_sources': self.updated_sources
        }
        
        # Save report
        report_path = Path('reports')
        report_path.mkdir(exist_ok=True)
        
        report_file = report_path / f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n📊 Verification Summary:")
        print(f"  Total sources: {total}")
        print(f"  Verified: {verified}")
        print(f"  Updated: {updated}")
        print(f"  Failed: {len(self.failed_sources)}")
        
        if self.failed_sources:
            print(f"\n❌ Failed sources:")
            for fail in self.failed_sources[:5]:
                print(f"  - {fail['evidence_id']}: {fail['url'][:50]}... ({fail['error']})")
            if len(self.failed_sources) > 5:
                print(f"  ... and {len(self.failed_sources) - 5} more")
        
        if self.updated_sources:
            print(f"\n🔄 Updated sources:")
            for update in self.updated_sources[:5]:
                print(f"  - {update['evidence_id']}: content changed")
            if len(self.updated_sources) > 5:
                print(f"  ... and {len(self.updated_sources) - 5} more")
        
        print(f"\n📄 Full report saved to: {report_file}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Verify evidence sources')
    parser.add_argument('--check-new-only', action='store_true', 
                       help='Only check sources not verified in last 7 days')
    args = parser.parse_args()
    
    verifier = SourceVerifier()
    success = verifier.verify_all_sources(check_new_only=args.check_new_only)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())