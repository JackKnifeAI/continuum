#!/usr/bin/env python3
"""
Example PostHog Analytics Integration for CONTINUUM

Demonstrates how to integrate PostHog analytics into your CONTINUUM application.
"""

# ============================================================================
# EXAMPLE 1: Basic Event Tracking
# ============================================================================

from continuum.core.analytics import (
    get_analytics,
    track_user_signup,
    track_user_login,
    track_memory_create,
    track_memory_search,
    track_federation_join,
)

# Track user signup
def register_user(user_id: str, email: str, plan: str = "free"):
    """Register a new user"""
    # ... user registration logic ...

    # Track signup event
    track_user_signup(user_id, plan=plan)

    # Identify user with properties
    analytics = get_analytics()
    analytics.identify(user_id, {
        "plan": plan,
        "signup_date": "2025-12-06T00:00:00Z",
        "account_age": 0,
    })


# Track user login
def login_user(user_id: str):
    """Authenticate user"""
    # ... authentication logic ...

    # Track login event
    track_user_login(user_id)


# Track memory operations
def create_memory(user_id: str, memory_data: dict):
    """Create a new memory"""
    # ... memory creation logic ...

    # Track memory creation
    track_memory_create(
        user_id,
        memory_type="concept",
        size_bytes=len(str(memory_data)),
    )


# Track search
def search_memories(user_id: str, query: str):
    """Search for memories"""
    import time
    start_time = time.time()

    # ... search logic ...
    results = []  # your search results

    duration_ms = (time.time() - start_time) * 1000

    # Track search event
    track_memory_search(
        user_id,
        query=query,
        results_count=len(results),
        duration_ms=duration_ms,
    )

    return results


# ============================================================================
# EXAMPLE 2: FastAPI Integration with Middleware
# ============================================================================

from fastapi import FastAPI, Header, HTTPException
from continuum.api.middleware import AnalyticsMiddleware

app = FastAPI()

# Add analytics middleware (tracks all requests automatically)
app.add_middleware(AnalyticsMiddleware)


@app.post("/api/memories")
async def create_memory_endpoint(
    memory: dict,
    x_user_id: str = Header(None),
):
    """Create memory endpoint with automatic tracking"""
    if not x_user_id:
        raise HTTPException(status_code=401, message="Unauthorized")

    # Create memory
    memory_id = "mem_123"  # your logic here

    # Track additional event (beyond automatic API tracking)
    track_memory_create(x_user_id, memory_type="concept", size_bytes=1024)

    return {"id": memory_id, "status": "created"}


@app.get("/api/memories/search")
async def search_endpoint(
    query: str,
    x_user_id: str = Header(None),
):
    """Search endpoint with tracking"""
    import time
    start_time = time.time()

    # Search logic
    results = search_memories(x_user_id, query)

    duration_ms = (time.time() - start_time) * 1000

    # Tracking already done in search_memories()
    return {"results": results, "count": len(results)}


# ============================================================================
# EXAMPLE 3: Flask Integration
# ============================================================================

from flask import Flask, request, jsonify
from continuum.api.middleware import FlaskAnalyticsMiddleware

flask_app = Flask(__name__)

# Wrap with analytics middleware
flask_app.wsgi_app = FlaskAnalyticsMiddleware(flask_app.wsgi_app)


@flask_app.route("/api/memories", methods=["POST"])
def flask_create_memory():
    """Flask endpoint with analytics"""
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    memory_data = request.json

    # Track event
    track_memory_create(user_id, memory_type="concept", size_bytes=len(str(memory_data)))

    return jsonify({"id": "mem_123", "status": "created"})


# ============================================================================
# EXAMPLE 4: Feature Flags
# ============================================================================

from continuum.core.analytics import get_analytics


def process_search(user_id: str, query: str):
    """Use feature flags to control behavior"""
    analytics = get_analytics()

    # Check if user has access to new search algorithm
    use_new_algorithm = analytics.get_feature_flag(
        user_id,
        "new_search_algorithm",
        default=False,
    )

    if use_new_algorithm:
        # Use enhanced semantic search
        results = new_semantic_search(query)
    else:
        # Use standard search
        results = standard_search(query)

    return results


def enable_beta_features(user_id: str):
    """Check multiple feature flags"""
    analytics = get_analytics()

    # Get all flags at once
    flags = analytics.get_feature_flags(user_id)

    features = {
        "beta_features": flags.get("beta_features", False),
        "federation_v2": flags.get("federation_v2", False),
        "realtime_sync": flags.get("realtime_sync", False),
    }

    return features


# ============================================================================
# EXAMPLE 5: Custom Event with Decorator
# ============================================================================

from continuum.core.analytics import track_decorator


@track_decorator(
    "custom_operation",
    extract_properties=lambda args, kwargs: {
        "operation_type": kwargs.get("op_type"),
        "data_size": len(kwargs.get("data", [])),
    },
)
def perform_custom_operation(user_id: str, op_type: str, data: list):
    """Custom operation with automatic tracking"""
    # Your logic here
    result = process_data(data)

    # Decorator automatically tracks:
    # - Event name: "custom_operation"
    # - Properties: operation_type, data_size, success, duration_ms
    # - User: user_id

    return result


# ============================================================================
# EXAMPLE 6: User Properties and Segmentation
# ============================================================================

def update_user_plan(user_id: str, new_plan: str):
    """Update user subscription plan"""
    analytics = get_analytics()

    # Update user properties
    analytics.identify(user_id, {
        "plan": new_plan,
        "plan_updated_at": "2025-12-06T00:00:00Z",
    })

    # Track event
    analytics.track(user_id, "plan_upgraded", {
        "new_plan": new_plan,
        "previous_plan": "free",
    })


def track_user_metrics(user_id: str):
    """Update user engagement metrics"""
    analytics = get_analytics()

    # Calculate metrics
    total_memories = get_memory_count(user_id)
    account_age = get_account_age_days(user_id)
    is_federation_user = is_in_federation(user_id)

    # Update properties for segmentation
    analytics.identify(user_id, {
        "total_memories": total_memories,
        "account_age": account_age,
        "federation_participant": is_federation_user,
    })


# ============================================================================
# EXAMPLE 7: Error Tracking
# ============================================================================

from continuum.core.analytics import track_error


def risky_operation(user_id: str):
    """Operation with error tracking"""
    try:
        # Your logic here
        result = perform_operation()
        return result
    except ValueError as e:
        # Track non-fatal error
        track_error(
            user_id,
            error_type="ValueError",
            context="risky_operation",
            fatal=False,
        )
        # Handle error
        return None
    except Exception as e:
        # Track fatal error
        track_error(
            user_id,
            error_type=type(e).__name__,
            context="risky_operation",
            fatal=True,
        )
        raise


# ============================================================================
# EXAMPLE 8: Session Tracking
# ============================================================================

from continuum.core.analytics import track_session_start, track_session_end
import time


class UserSession:
    """User session with analytics"""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.start_time = None

    def start(self):
        """Start session"""
        self.start_time = time.time()
        track_session_start(self.user_id)

    def end(self):
        """End session"""
        if self.start_time:
            duration_seconds = time.time() - self.start_time
            track_session_end(self.user_id, duration_seconds)


# Usage
def user_workflow(user_id: str):
    """Complete user workflow with session tracking"""
    session = UserSession(user_id)
    session.start()

    try:
        # User actions
        login_user(user_id)
        create_memory(user_id, {"concept": "test"})
        search_memories(user_id, "warp drive")
    finally:
        # Always end session
        session.end()


# ============================================================================
# EXAMPLE 9: Configuration
# ============================================================================

from continuum.core.analytics import AnalyticsConfig, set_analytics, Analytics


def configure_analytics_custom():
    """Custom analytics configuration"""
    config = AnalyticsConfig(
        api_key="phc_your_api_key",
        host="https://app.posthog.com",
        enabled=True,
        anonymize_users=True,
        opt_out=False,
        capture_ip=False,
        batch_size=20,  # Batch more events
        flush_interval=5.0,  # Flush every 5 seconds
    )

    analytics = Analytics(config)
    set_analytics(analytics)


def configure_analytics_from_env():
    """Load analytics from environment variables"""
    import os

    # Set environment variables
    os.environ["POSTHOG_API_KEY"] = "phc_your_key"
    os.environ["POSTHOG_HOST"] = "https://app.posthog.com"
    os.environ["CONTINUUM_ANALYTICS_ENABLED"] = "true"

    # Analytics will automatically load from env
    analytics = get_analytics()


def opt_out_user(user_id: str):
    """Allow user to opt out of analytics"""
    import os

    os.environ["CONTINUUM_ANALYTICS_OPT_OUT"] = "true"

    # Create new analytics instance with opt-out
    config = AnalyticsConfig.load()
    analytics = Analytics(config)
    set_analytics(analytics)


# ============================================================================
# EXAMPLE 10: Testing with Mock Analytics
# ============================================================================

def setup_test_analytics():
    """Disable analytics for testing"""
    config = AnalyticsConfig(enabled=False)
    set_analytics(Analytics(config))


def test_user_signup():
    """Test user signup without real analytics"""
    # Disable analytics
    setup_test_analytics()

    # Test logic
    user_id = "test_user_123"
    register_user(user_id, "test@example.com", plan="free")

    # No analytics events sent
    # Test assertions...
    assert True


# ============================================================================
# Placeholder functions for examples
# ============================================================================

def process_data(data):
    return {"processed": len(data)}

def new_semantic_search(query):
    return [{"result": "mock"}]

def standard_search(query):
    return [{"result": "mock"}]

def get_memory_count(user_id):
    return 100

def get_account_age_days(user_id):
    return 30

def is_in_federation(user_id):
    return True

def perform_operation():
    return {"success": True}


if __name__ == "__main__":
    print("PostHog Analytics Integration Examples")
    print("=" * 50)
    print()
    print("See function implementations above for:")
    print("1. Basic event tracking")
    print("2. FastAPI middleware integration")
    print("3. Flask middleware integration")
    print("4. Feature flags")
    print("5. Custom events with decorators")
    print("6. User properties and segmentation")
    print("7. Error tracking")
    print("8. Session tracking")
    print("9. Custom configuration")
    print("10. Testing with mocks")
    print()
    print("For complete documentation, see:")
    print("  - deploy/posthog/README.md")
    print("  - deploy/posthog/INTEGRATION_SUMMARY.md")
    print("  - continuum/core/analytics.py")
