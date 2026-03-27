PROMPTS = {
    'risk_explanation': "Explain why this trading order was rejected. Be concise, factual, and output JSON with keys: summary, risk_factors, suggested_next_steps. Payload: {payload}",
    'strategy_summary': "Summarize this backtest result for a quant researcher. Output JSON with keys: summary, strengths, weaknesses, follow_ups. Payload: {payload}",
    'portfolio_qa': "Answer this portfolio risk question using the provided portfolio/risk payload. Output JSON with keys: answer, key_risks, recommendations. Payload: {payload}",
}
