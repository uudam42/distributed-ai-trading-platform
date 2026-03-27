def mock_analysis(analysis_type: str, payload: dict) -> dict:
    if analysis_type == 'risk_explanation':
        return {
            'summary': 'Order rejected because configured risk checks failed.',
            'risk_factors': ['insufficient buying power', 'pre-trade policy block'],
            'suggested_next_steps': ['reduce order size', 'review account limits'],
        }
    if analysis_type == 'strategy_summary':
        return {
            'summary': f"Strategy {payload.get('strategy', 'unknown')} completed with deterministic mock analysis.",
            'strengths': ['stable test output', 'works without vLLM'],
            'weaknesses': ['not model-generated', 'limited nuance'],
            'follow_ups': ['run with real vLLM for richer language output'],
        }
    return {
        'answer': 'Portfolio risk appears moderate under the provided payload.',
        'key_risks': ['inventory concentration', 'PnL volatility'],
        'recommendations': ['reduce directional exposure', 'review concentration limits'],
    }
