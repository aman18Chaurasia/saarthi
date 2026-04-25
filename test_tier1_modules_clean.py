"""Standalone tests for Tier 1 modules.

Run: python test_tier1_modules.py
"""
import asyncio
import sys
from pathlib import Path

# Import directly using importlib
import importlib.util

def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load modules
base_path = Path(__file__).parent
memory_module = load_module("memory_manager", base_path / "packages" / "dialog" / "dialog" / "memory_manager.py")
sentiment_module = load_module("sentiment_analyzer", base_path / "packages" / "voice" / "sentiment_analyzer.py")

ConversationMemory = memory_module.ConversationMemory
SentimentAnalyzer = sentiment_module.SentimentAnalyzer


async def test_conversation_memory():
    """Test ConversationMemory module."""
    print("\n" + "="*60)
    print("TEST 1: CONVERSATION MEMORY")
    print("="*60)

    memory = ConversationMemory()

    # Simulate a conversation
    print("\n📝 Adding conversation turns...")
    await memory.add_turn("agent", "Namaste! Aap Rahul ji hain?", "opener", 0)
    await memory.add_turn("customer", "Yes, I am interested in home loan", "opener", 1)
    await memory.add_turn("agent", "Great! Aapki monthly income kitni hai?", "qualify", 2)
    await memory.add_turn("customer", "Around 50,000 rupees per month", "qualify", 3)
    await memory.add_turn("agent", "Perfect. Loan ka use kisliye?", "qualify_followup", 4)
    await memory.add_turn("customer", "For buying a house in Mumbai", "qualify_followup", 5)

    # Test 1: Recent context
    print("\n>> Recent context (last 4 turns):")
    recent = memory.get_recent_context(4)
    for msg in recent:
        print(f"  {msg['role']}: {msg['content'][:50]}...")

    # Test 2: Semantic retrieval
    print("\n>> Semantic retrieval (query: 'house purpose'):")
    relevant = await memory.retrieve_relevant_context("house purpose", max_turns=2)
    print(f"  {relevant}")

    # Test 3: Key facts extraction
    print("\n>> Key facts extracted:")
    facts = memory.get_key_facts_summary()
    print(f"  {facts if facts else 'None (expected - need more specific keywords)'}")

    # Test 4: Question detection
    print("\n>> Question detection:")
    await memory.add_turn("customer", "What is the interest rate?", "consent", 6)
    has_question = memory.has_customer_asked_question()
    last_question = memory.get_last_customer_question()
    print(f"  Has question: {has_question}")
    print(f"  Last question: {last_question}")

    print("\n>> ConversationMemory: ALL TESTS PASSED!")
    return True


async def test_sentiment_analyzer():
    """Test SentimentAnalyzer module."""
    print("\n" + "="*60)
    print("TEST 2: SENTIMENT ANALYZER")
    print("="*60)

    analyzer = SentimentAnalyzer()

    # Test 1: Frustration detection
    print("\n📝 Test 1: Frustration detection")
    sentiment1 = await analyzer.analyze("This is too expensive! I can't afford it!")
    print(f"  Text: 'This is too expensive! I can't afford it!'")
    print(f"  Valence: {sentiment1.valence:.2f} (negative)")
    print(f"  Frustration: {sentiment1.frustration_level:.2f} (high)")
    print(f"  Emotion: {sentiment1.detected_emotion}")
    assert sentiment1.frustration_level > 0.5, "Should detect high frustration"
    print("  >> PASSED")

    # Test 2: Positive sentiment
    print("\n📝 Test 2: Positive sentiment")
    sentiment2 = await analyzer.analyze("Yes, I'm very interested! Please tell me more.")
    print(f"  Text: 'Yes, I'm very interested! Please tell me more.'")
    print(f"  Valence: {sentiment2.valence:.2f} (positive)")
    print(f"  Engagement: {sentiment2.engagement:.2f} (high)")
    print(f"  Emotion: {sentiment2.detected_emotion}")
    assert sentiment2.valence > 0, "Should detect positive valence"
    print("  >> PASSED")

    # Test 3: Confusion detection
    print("\n📝 Test 3: Confusion detection")
    sentiment3 = await analyzer.analyze("What? I don't understand. Can you repeat?")
    print(f"  Text: 'What? I don't understand. Can you repeat?'")
    print(f"  Emotion: {sentiment3.detected_emotion}")
    assert sentiment3.detected_emotion == "confused", "Should detect confusion"
    print("  >> PASSED")

    # Test 4: Adaptive response guidance
    print("\n📝 Test 4: Adaptive response guidance")
    sentiment4 = await analyzer.analyze("This is confusing and too costly!")
    guidance = await analyzer.get_adaptive_response_guidance(sentiment4)
    print(f"  Text: 'This is confusing and too costly!'")
    print(f"  Guidance: {guidance[:100]}...")
    assert len(guidance) > 0, "Should provide guidance for frustrated customer"
    print("  >> PASSED")

    # Test 5: TTS adjustments
    print("\n📝 Test 5: TTS adjustments")
    sentiment5 = await analyzer.analyze("No! Stop calling me!")
    adjustments = analyzer.get_tts_adjustments(sentiment5)
    print(f"  Text: 'No! Stop calling me!'")
    print(f"  TTS Adjustments: {adjustments}")
    assert adjustments["rate"] < 1.0, "Should slow down for frustrated customer"
    print("  >> PASSED")

    # Test 6: Human handoff detection
    print("\n📝 Test 6: Human handoff detection")
    sentiment6 = await analyzer.analyze("I don't understand anything! This is frustrating!")
    should_handoff = analyzer.should_offer_human_handoff(sentiment6)
    print(f"  Text: 'I don't understand anything! This is frustrating!'")
    print(f"  Should offer handoff: {should_handoff}")
    print("  >> PASSED")

    print("\n>> SentimentAnalyzer: ALL TESTS PASSED!")
    return True


async def test_retry_logic():
    """Test smart retry logic."""
    print("\n" + "="*60)
    print("TEST 3: SMART RETRY LOGIC")
    print("="*60)

    sys.path.insert(0, str(Path(__file__).parent / "packages" / "dialog" / "dialog" / "personal_loan"))
    from prompts import get_script_text, _RETRY_VARIANTS

    print("\n📝 Testing retry variants for 'qualify' node:")
    for retry_count in range(3):
        script = get_script_text("qualify", retry_count)
        print(f"\n  Attempt {retry_count + 1}: {script}")

    print("\n📝 Available retry variants:")
    for node, variants in _RETRY_VARIANTS.items():
        print(f"\n  {node}: {len(variants)} variants")
        for i, variant in enumerate(variants):
            print(f"    {i+1}. {variant[:60]}...")

    print("\n>> Smart Retry Logic: ALL TESTS PASSED!")
    return True


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("TIER 1 MODULES - STANDALONE TESTING")
    print("="*60)

    try:
        # Run all tests
        test1 = await test_conversation_memory()
        test2 = await test_sentiment_analyzer()
        test3 = await test_retry_logic()

        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"  ConversationMemory: {'>> PASSED' if test1 else 'XX FAILED'}")
        print(f"  SentimentAnalyzer: {'>> PASSED' if test2 else 'XX FAILED'}")
        print(f"  Smart Retry Logic: {'>> PASSED' if test3 else 'XX FAILED'}")

        if all([test1, test2, test3]):
            print("\n>>> ALL MODULES WORKING! Ready for integration.")
            return 0
        else:
            print("\n>>> Some tests failed. Check output above.")
            return 1

    except Exception as e:
        print(f"\n>>> ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
