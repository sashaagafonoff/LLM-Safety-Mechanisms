import requests
import hashlib
import json
from datetime import datetime
from pathlib import Path

def calculate_hash(content):
    """Calculate SHA-256 hash of content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def verify_url(url):
    """Check if URL is accessible and get content hash"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (LLM-Safety-Mechanisms/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                'accessible': True,
                'status_code': 200,
                'content_hash': calculate_hash(response.text[:10000]),  # First 10KB
                'content_type': response.headers.get('Content-Type', ''),
                'last_modified': response.headers.get('Last-Modified', '')
            }
        else:
            return {
                'accessible': False,
                'status_code': response.status_code,
                'error': f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            'accessible': False,
            'error': str(e)
        }

def verify_all_sources():
    """Verify all sources in evidence.json"""
    with open('data/evidence.json', 'r') as f:
        evidence = json.load(f)
    
    results = []
    updated_count = 0
    
    for record in evidence:
        print(f"\nVerifying {record['id']}...")
        
        for source in record['sourceUrls']:
            print(f"  Checking {source['url'][:50]}...")
            result = verify_url(source['url'])
            
            if result['accessible']:
                # Update hash and verification date
                source['sourceHash'] = result['content_hash']
                source['lastVerified'] = datetime.now().strftime('%Y-%m-%d')
                updated_count += 1
                print(f"    ✅ Accessible (hash: {result['content_hash'][:8]}...)")
            else:
                print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                results.append({
                    'evidence_id': record['id'],
                    'url': source['url'],
                    'error': result.get('error')
                })
    
    # Save updated evidence
    with open('data/evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    
    print(f"\n✅ Updated {updated_count} source hashes")
    
    if results:
        print(f"\n⚠️  {len(results)} sources failed verification:")
        for r in results:
            print(f"  - {r['evidence_id']}: {r['error']}")
    
    return len(results) == 0

if __name__ == "__main__":
    verify_all_sources()