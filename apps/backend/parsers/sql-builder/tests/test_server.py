"""Tests for gRPC server in src/server.py"""

import sys
from unittest.mock import MagicMock

# Mock proto_utils ONLY for this test module before importing server
_mock_modules = [
    "proto_utils",
    "proto_utils.generated",
    "proto_utils.generated.parsers",
    "proto_utils.parsers",
]

for mod_name in _mock_modules:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Set up proto_utils attributes AFTER creating mocks
mock_grpc_module = sys.modules["proto_utils.generated.parsers"]
mock_grpc_module.sql_builder_pb2 = MagicMock()
mock_grpc_module.sql_builder_pb2_grpc = MagicMock()


# Create a real base class for SQLBuilderServicer (not a mock)
class MockSQLBuilderServicer:
    """Mock base class for gRPC servicer"""

    pass


mock_grpc_module.sql_builder_pb2_grpc.SQLBuilderServicer = (
    MockSQLBuilderServicer
)

# Mock parsers utilities
sys.modules["proto_utils.parsers"].DDLGeneratorSerde = MagicMock()
sys.modules["proto_utils.parsers"].SQLBuilderSerde = MagicMock()

# Now import server with proper base class
from src.server import SQLBuilderServicer  # noqa: E402


class TestSQLBuilderServicer:
    """Tests for SQLBuilderServicer gRPC methods"""

    def test_servicer_can_be_instantiated(self):
        # Excel input: Servicer instantiation
        servicer = SQLBuilderServicer()
        assert servicer is not None

    def test_servicer_has_build_sql_method(self):
        # Excel input: BuildSQL method exists
        servicer = SQLBuilderServicer()
        assert hasattr(servicer, "BuildSQL")
        assert callable(getattr(servicer, "BuildSQL"))
