"""Kafka topics follow <domain>.<event>.v1.

Primary topics:
- orders.received.v1: new client order entered and persisted
- risk.order.approved.v1: risk accepted an order
- risk.order.rejected.v1: risk rejected an order
- orders.accepted.v1: order cleared for matching
- trades.executed.v1: matching engine produced an execution

Migration compatibility:
- risk.order.aproved.v1: deprecated misspelled topic kept temporarily for compatibility

DLQ convention:
- <topic>.dlq: failed messages after retry exhaustion
"""

ORDERS_RECEIVED = 'orders.received.v1'
RISK_ORDER_APPROVED = 'risk.order.approved.v1'
RISK_ORDER_APPROVED_LEGACY = 'risk.order.aproved.v1'
RISK_ORDER_REJECTED = 'risk.order.rejected.v1'
ORDERS_ACCEPTED = 'orders.accepted.v1'
TRADES_EXECUTED = 'trades.executed.v1'


def dlq_topic(topic: str) -> str:
    return f'{topic}.dlq'


# TODO(Phase2.2+): remove RISK_ORDER_APPROVED_LEGACY after migration window closes.
