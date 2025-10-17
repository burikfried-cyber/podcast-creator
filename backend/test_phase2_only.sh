#!/bin/bash
# Run only Phase 2 unit tests
pytest tests/unit/test_api_clients.py tests/unit/test_orchestrator.py tests/unit/test_quality_assessor.py tests/unit/test_cost_tracker.py tests/unit/test_circuit_breaker.py -v
