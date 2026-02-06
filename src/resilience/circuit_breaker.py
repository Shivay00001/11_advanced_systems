"""
Circuit Breaker - Fault tolerance pattern implementation.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

import structlog

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(str, Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    half_open_max_calls: int = 3


@dataclass
class CircuitBreakerState:
    """Internal circuit breaker state."""
    
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    half_open_calls: int = 0


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by failing fast when
    a service is unhealthy.
    
    Usage:
        circuit = CircuitBreaker("user-service")
        
        @circuit.protect
        async def call_user_service():
            return await http_client.get("/users")
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit name for logging
            config: Optional configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState()
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state.state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal)."""
        return self._state.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self._state.state == CircuitState.OPEN
    
    async def _should_allow_request(self) -> bool:
        """Determine if request should be allowed."""
        async with self._lock:
            if self._state.state == CircuitState.CLOSED:
                return True
            
            if self._state.state == CircuitState.OPEN:
                # Check if timeout has passed
                if self._state.last_failure_time:
                    elapsed = time.time() - self._state.last_failure_time
                    if elapsed >= self.config.timeout_seconds:
                        self._transition_to_half_open()
                        return True
                return False
            
            # Half-open: allow limited requests
            if self._state.half_open_calls < self.config.half_open_max_calls:
                self._state.half_open_calls += 1
                return True
            
            return False
    
    async def _record_success(self) -> None:
        """Record successful call."""
        async with self._lock:
            if self._state.state == CircuitState.HALF_OPEN:
                self._state.success_count += 1
                if self._state.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self._state.state == CircuitState.CLOSED:
                # Reset failure count on success
                self._state.failure_count = 0
    
    async def _record_failure(self, error: Exception) -> None:
        """Record failed call."""
        async with self._lock:
            self._state.failure_count += 1
            self._state.last_failure_time = time.time()
            
            logger.warning(
                "circuit_breaker_failure",
                circuit=self.name,
                failure_count=self._state.failure_count,
                error=str(error),
            )
            
            if self._state.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            elif self._state.state == CircuitState.CLOSED:
                if self._state.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
    
    def _transition_to_open(self) -> None:
        """Transition to open state."""
        logger.warning("circuit_breaker_opened", circuit=self.name)
        self._state.state = CircuitState.OPEN
        self._state.success_count = 0
        self._state.half_open_calls = 0
    
    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        logger.info("circuit_breaker_half_open", circuit=self.name)
        self._state.state = CircuitState.HALF_OPEN
        self._state.half_open_calls = 0
        self._state.success_count = 0
    
    def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        logger.info("circuit_breaker_closed", circuit=self.name)
        self._state.state = CircuitState.CLOSED
        self._state.failure_count = 0
        self._state.success_count = 0
    
    def protect(self, func: F) -> F:
        """
        Decorator to protect a function with circuit breaker.
        
        Args:
            func: Async function to protect
            
        Returns:
            Protected function
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not await self._should_allow_request():
                raise CircuitBreakerOpen(
                    f"Circuit '{self.name}' is open"
                )
            
            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except Exception as e:
                await self._record_failure(e)
                raise
        
        return wrapper  # type: ignore


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


# Registry for circuit breakers
_circuits: dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.
    
    Args:
        name: Circuit name
        config: Optional configuration
        
    Returns:
        Circuit breaker instance
    """
    if name not in _circuits:
        _circuits[name] = CircuitBreaker(name, config)
    return _circuits[name]
