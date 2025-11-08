from enum import Enum

class AgentProvider(Enum):
    LANGRAPH = "langgraph"

# Test constructing from value
try:
    result = AgentProvider("langgraph")
    print(f"✅ Success: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# Correct way with member name
try:
    result = AgentProvider["LANGRAPH"]
    print(f"✅ By name: {result}")
except Exception as e:
    print(f"❌ Error: {e}")
