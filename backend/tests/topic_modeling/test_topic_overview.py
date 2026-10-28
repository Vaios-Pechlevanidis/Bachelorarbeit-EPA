# Hinweis: Teile dieser Datei wurden mit Claude Code (Anthropic) erstellt.
# Unterstützung bei der Implementierung des Prototyps im zweiten Zyklus
# (Frontend, Tests, Auswertungsskripte); Vorschlag der Referenzzeiträume
# nach dem Annotationsprotokoll (Abschnitt 3.6.1)

import requests
import json

BASE_URL = "http://localhost:8000"
COMPANY_ID = 1

def test_topic_overview():
    print(f"🧪 Testing Topic Overview API for Company {COMPANY_ID}")
    print("=" * 60)
    
    try:
        url = f"{BASE_URL}/api/analytics/company/{COMPANY_ID}/topic-overview"
        print(f"📡 Requesting: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Request successful!")
            data = response.json()
            
            print(f"\n📊 Summary:")
            print(f"   Total Topics: {data.get('total_topics', 0)}")
            print(f"   Total Reviews: {data.get('total_reviews', 0)}")
            
            topics = data.get('topics', [])
            if topics:
                print(f"\n📋 Found Topics:")
                for topic in topics:
                    sentiment_emoji = {
                        "Positiv": "😊",
                        "Neutral": "😐",
                        "Negativ": "😟"
                    }.get(topic['sentiment'], "❓")
                    
                    print(f"\n   {sentiment_emoji} {topic['topic']}")
                    print(f"      Frequency: {topic['frequency']} mentions")
                    print(f"      Avg Rating: {topic['avgRating']}/5")
                    print(f"      Sentiment: {topic['sentiment']}")
                    print(f"      Example: {topic['example'][:60]}...")
                    
                    if topic.get('timelineData'):
                        timeline = topic['timelineData']
                        print(f"      Timeline: {timeline[0]['month']}={timeline[0]['rating']} → {timeline[-1]['month']}={timeline[-1]['rating']}")
                    
                    if topic.get('typicalStatements') and len(topic['typicalStatements']) > 0:
                        print(f"      Statements: {len(topic['typicalStatements'])} found")
                        print(f"         - {topic['typicalStatements'][0][:60]}...")
            else:
                print("\n⚠️  No topics found")
            
            print(f"\n📄 Full JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("   Make sure the backend is running:")
        print("   cd backend && uvicorn main:app --reload")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_multiple_companies():
    print("\n" + "=" * 60)
    print("🔍 Testing multiple companies")
    print("=" * 60)
    
    for company_id in [1, 2, 3]:
        print(f"\n📍 Company {company_id}:")
        try:
            url = f"{BASE_URL}/api/analytics/company/{company_id}/topic-overview"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ {data.get('total_topics', 0)} topics, {data.get('total_reviews', 0)} reviews")
            else:
                print(f"   ❌ Error {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║          Topic Overview API Test Script                    ║
║                                                             ║
║  Make sure your backend is running:                        ║
║  $ cd backend && uvicorn main:app --reload                 ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    test_topic_overview()
    
    print("\n✨ Test completed!\n")
