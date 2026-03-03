"""
test_demo.py
Quick demo test — runs all 5 trade questions through the agent.
Use this to verify everything works before recording the demo.
Run: python test_demo.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agent.graph import ask

DEMO_QUESTIONS = [
    ("Trade Failure",          "What happened to trade 12345?"),
    ("Duplicate Trade",        "Why was trade 22222 rejected?"),
    ("System Outage",          "What is going on with trade 33333?"),
    ("Slow Settlement",        "Trade 44444 settled but something looks wrong?"),
    ("Risk Engine Rejection",  "Why did trade 55555 fail the risk check?"),
]

def run():
    print("\n" + "="*70)
    print("  AskOps by AskOps by RaveMinds — Demo Test")
    print("="*70)

    for scenario, question in DEMO_QUESTIONS:
        print(f"\n📌 Scenario: {scenario}")
        print(f"   Question: {question}")
        print("-"*70)
        answer = ask(question)
        print(answer)
        print()

if __name__ == "__main__":
    run()
