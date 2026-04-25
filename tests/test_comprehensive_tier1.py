"""Comprehensive Tier 1 feature tests.

Tests all modules in realistic conversation scenarios.
"""
import asyncio
import sys
from pathlib import Path

# Load modules
import importlib.util

def load_module(name, file_path):
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base = Path(__file__).parent.parent
memory_mod = load_module('memory', base / 'packages' / 'dialog' / 'dialog' / 'memory_manager.py')
sentiment_mod = load_module('sentiment', base / 'packages' / 'voice' / 'sentiment_analyzer.py')
personalization_mod = load_module('personalization', base / 'packages' / 'dialog' / 'dialog' / 'personalization.py')

ConversationMemory = memory_mod.ConversationMemory
SentimentAnalyzer = sentiment_mod.SentimentAnalyzer
PersonalizationEngine = personalization_mod.PersonalizationEngine
CustomerProfile = personalization_mod.CustomerProfile


async def test_scenario_1_frustrated_customer():
    """Test: Customer gets frustrated about price."""
    print("\n" + "="*60)
    print("SCENARIO 1: Frustrated Customer")
    print("="*60)

    memory = ConversationMemory()
    analyzer = SentimentAnalyzer()

    # Simulate conversation
    turns = [
        ("agent", "Namaste! Aap Rahul ji hain?", "opener", 0),
        ("customer", "Yes, what do you want?", "opener", 1),
        ("agent", "Personal loan offer ke baare mein baat karni thi", "identity_confirm", 2),
        ("customer", "I'm not interested in expensive loans!", "identity_confirm", 3),
    ]

    for speaker, text, node, idx in turns:
        await memory.add_turn(speaker, text, node, idx)

    # Analyze last customer utterance
    sentiment = await analyzer.analyze("I'm not interested in expensive loans!")

    print(f"\nCustomer: 'I'm not interested in expensive loans!'")
    print(f">> Frustration Level: {sentiment.frustration_level:.2f}")
    print(f">> Emotion: {sentiment.detected_emotion}")
    print(f">> Valence: {sentiment.valence:.2f}")

    # Get adaptive guidance
    guidance = await analyzer.get_adaptive_response_guidance(sentiment)
    print(f"\n>> Adaptive Guidance:")
    print(f"   {guidance[:150]}...")

    # Check TTS adjustments
    tts_adj = analyzer.get_tts_adjustments(sentiment)
    print(f"\n>> TTS Adjustments:")
    print(f"   Rate: {tts_adj['rate']:.2f} (slower for frustrated)")
    print(f"   Pitch: {tts_adj['pitch_shift']:.0f} Hz (lower pitch)")

    # Check if should offer handoff
    should_handoff = analyzer.should_offer_human_handoff(sentiment)
    print(f"\n>> Should offer human handoff: {should_handoff}")

    assert sentiment.frustration_level > 0.3, "Should detect frustration"
    assert tts_adj['rate'] < 1.0, "Should slow down"
    print("\n>> PASS: Correctly detected frustration and adapted")
    return True


async def test_scenario_2_engaged_customer():
    """Test: Customer is very engaged and asking questions."""
    print("\n" + "="*60)
    print("SCENARIO 2: Engaged Customer")
    print("="*60)

    memory = ConversationMemory()
    analyzer = SentimentAnalyzer()

    # Engaged conversation
    turns = [
        ("agent", "Aapki monthly income kitni hai?", "qualify", 0),
        ("customer", "50,000. Tell me more about interest rates!", "qualify", 1),
        ("agent", "Starting at 9.5%", "qualify", 2),
        ("customer", "That's good! What about tenure? Can I get more details?", "qualify_followup", 3),
    ]

    for speaker, text, node, idx in turns:
        await memory.add_turn(speaker, text, node, idx)

    # Analyze engagement
    sentiment = await analyzer.analyze("That's good! What about tenure? Can I get more details?")

    print(f"\nCustomer: 'That's good! What about tenure? Can I get more details?'")
    print(f">> Engagement: {sentiment.engagement:.2f}")
    print(f">> Emotion: {sentiment.detected_emotion}")
    print(f">> Valence: {sentiment.valence:.2f}")

    # Should detect question
    has_question = memory.has_customer_asked_question()
    last_q = memory.get_last_customer_question()

    print(f"\n>> Has question: {has_question}")
    print(f">> Last question: {last_q}")

    assert sentiment.engagement > 0.5, "Should detect high engagement"
    assert has_question, "Should detect question"
    assert sentiment.detected_emotion in ["interested", "excited"], "Should be interested"
    print("\n>> PASS: Correctly detected engagement and questions")
    return True


async def test_scenario_3_memory_recall():
    """Test: Agent recalls information from earlier in conversation."""
    print("\n" + "="*60)
    print("SCENARIO 3: Memory Recall")
    print("="*60)

    memory = ConversationMemory()

    # Long conversation with key fact early on
    turns = [
        ("customer", "I need loan for my daughter's education abroad", "qualify_followup", 0),
        ("agent", "Great! Which country?", "qualify_followup", 1),
        ("customer", "USA, for engineering degree", "qualify_followup", 2),
        ("agent", "Excellent. Your income?", "qualify", 3),
        ("customer", "60,000 per month", "qualify", 4),
        ("agent", "Any existing loans?", "qualify", 5),
        ("customer", "No, this is first", "qualify", 6),
        ("agent", "Property owned?", "qualify", 7),
        ("customer", "Yes, one house", "qualify", 8),
    ]

    for speaker, text, node, idx in turns:
        await memory.add_turn(speaker, text, node, idx)

    # Now query about education (from turn 0!)
    context = await memory.retrieve_relevant_context("education daughter", max_turns=2)

    print(f"\nQuery: 'education daughter'")
    print(f">> Retrieved context:")
    print(f"{context}")

    # Check key facts
    facts = memory.get_key_facts_summary()
    print(f"\n>> Key facts extracted:")
    print(f"{facts}")

    assert "education" in context.lower() or "daughter" in context.lower(), "Should recall education mention"
    print("\n>> PASS: Successfully recalled information from turn 0")
    return True


async def test_scenario_4_personalization():
    """Test: Customer with history gets personalized approach."""
    print("\n" + "="*60)
    print("SCENARIO 4: Personalization")
    print("="*60)

    engine = PersonalizationEngine()

    # Create customer with history
    profile = CustomerProfile(
        customer_id="CUST001",
        objection_patterns=["interest_rate", "affordability"],
        successful_hooks=["family_security"],
        total_calls=3,
        qualified_calls=1,
        price_sensitivity=0.8,
    )

    # Get adaptive approach
    qualifying_guidance = engine.adapt_qualifying_approach(profile)

    print(f"\nCustomer Profile:")
    print(f"  Objections: {profile.objection_patterns}")
    print(f"  Successful hooks: {profile.successful_hooks}")
    print(f"  Price sensitivity: {profile.price_sensitivity}")

    print(f"\n>> Adaptive Qualifying Guidance:")
    print(f"{qualifying_guidance}")

    # Check language preference
    lang_pref = engine.get_language_preference(profile)
    print(f"\n>> Language preference: {lang_pref}")

    # Check product switching
    should_switch, product = engine.should_try_different_product(profile, "personal_loan")
    print(f"\n>> Should try different product: {should_switch}")

    assert "interest_rate" in qualifying_guidance.lower() or "rate" in qualifying_guidance.lower(), "Should address rate concern"
    print("\n>> PASS: Personalization working correctly")
    return True


async def test_scenario_5_retry_variants():
    """Test: Smart retry with different phrasings."""
    print("\n" + "="*60)
    print("SCENARIO 5: Smart Retry")
    print("="*60)

    # Load prompts module
    prompts_mod = load_module('prompts', base / 'packages' / 'dialog' / 'dialog' / 'personal_loan' / 'prompts.py')

    node = "qualify"
    print(f"\nNode: {node}")
    print(f"\nAttempt 1 (retry_count=0):")
    script1 = prompts_mod.get_script_text(node, retry_count=0)
    print(f"  {script1}")

    print(f"\nAttempt 2 (retry_count=1):")
    script2 = prompts_mod.get_script_text(node, retry_count=1)
    print(f"  {script2}")

    print(f"\nAttempt 3 (retry_count=2):")
    script3 = prompts_mod.get_script_text(node, retry_count=2)
    print(f"  {script3}")

    # Should be different
    assert script1 != script2, "Retry 1 should differ from original"
    assert script2 != script3, "Retry 2 should differ from retry 1"
    print("\n>> PASS: Retry variants working correctly")
    return True


async def test_scenario_6_emotion_progression():
    """Test: Track emotion changes through conversation."""
    print("\n" + "="*60)
    print("SCENARIO 6: Emotion Progression")
    print("="*60)

    analyzer = SentimentAnalyzer()

    # Conversation starts frustrated, becomes interested
    utterances = [
        ("Turn 1", "This is too expensive, I'm not interested!"),
        ("Turn 2", "Wait, you said it starts at just 2000 per month?"),
        ("Turn 3", "Hmm, that's actually affordable. Tell me more."),
        ("Turn 4", "Yes, I'm very interested! When can I apply?"),
    ]

    emotions = []
    for turn, text in utterances:
        sentiment = await analyzer.analyze(text)
        emotions.append((turn, text, sentiment.detected_emotion, sentiment.valence))
        print(f"\n{turn}: '{text[:50]}...'")
        print(f"  Emotion: {sentiment.detected_emotion}")
        print(f"  Valence: {sentiment.valence:.2f}")
        print(f"  Frustration: {sentiment.frustration_level:.2f}")

    # Should show progression: frustrated → interested
    first_emotion = emotions[0][2]
    last_emotion = emotions[-1][2]

    assert emotions[0][3] < 0, "Should start negative"
    assert emotions[-1][3] > 0, "Should end positive"
    print(f"\n>> Emotion progression: {first_emotion} → {last_emotion}")
    print(">> PASS: Emotion tracking works across conversation")
    return True


async def test_scenario_7_key_facts_extraction():
    """Test: Extract and track key facts."""
    print("\n" + "="*60)
    print("SCENARIO 7: Key Facts Extraction")
    print("="*60)

    memory = ConversationMemory()

    # Conversation with various key facts
    turns = [
        ("customer", "I'm looking for home loan", "identify", 0),
        ("customer", "But interest rates are too high!", "qualify", 1),
        ("customer", "I want this for buying house in Mumbai", "qualify_followup", 2),
        ("customer", "Also looking at car loan for future", "qualify_followup", 3),
    ]

    for speaker, text, node, idx in turns:
        await memory.add_turn(speaker, text, node, idx)

    # Check extracted facts
    facts = memory.get_key_facts_summary()

    print(f"\n>> Extracted Key Facts:")
    print(f"{facts if facts else 'None detected'}")

    # Manually check
    print(f"\n>> Fact details:")
    for fact_id, fact in memory.key_facts.items():
        print(f"  {fact.fact_type}: {fact.content} (importance: {fact.importance})")

    # Should have detected objection and interest
    fact_types = [f.fact_type for f in memory.key_facts.values()]
    assert "objection" in fact_types or "interest" in fact_types, "Should extract facts"
    print("\n>> PASS: Key facts extraction working")
    return True


async def main():
    """Run all test scenarios."""
    print("\n" + "="*60)
    print("COMPREHENSIVE TIER 1 TESTING")
    print("Testing realistic conversation scenarios")
    print("="*60)

    results = []
    scenarios = [
        ("Frustrated Customer", test_scenario_1_frustrated_customer),
        ("Engaged Customer", test_scenario_2_engaged_customer),
        ("Memory Recall", test_scenario_3_memory_recall),
        ("Personalization", test_scenario_4_personalization),
        ("Smart Retry", test_scenario_5_retry_variants),
        ("Emotion Progression", test_scenario_6_emotion_progression),
        ("Key Facts", test_scenario_7_key_facts_extraction),
    ]

    for name, test_fn in scenarios:
        try:
            result = await test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n>> ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)

    print(f"\n>> {passed_count}/{total_count} scenarios passed")

    if passed_count == total_count:
        print("\n==> ALL SCENARIOS PASSED! Features ready for production.")
        return 0
    else:
        print(f"\n==> {total_count - passed_count} scenarios failed. Review above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
