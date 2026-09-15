from __future__ import annotations

from fastmcp import FastMCP


mcp = FastMCP("Arithmetic Server")


def _as_number(value) -> float:
    """Convert a value to a number."""

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            pass

    raise TypeError(
        "Expected a number (int, float or numeric string)"
    )


@mcp.tool()
async def add(a: float, b: float) -> float:
    """Return a + b."""

    return _as_number(a) + _as_number(b)


@mcp.tool()
async def subtract(a: float, b: float) -> float:
    """Return a - b."""

    return _as_number(a) - _as_number(b)


@mcp.tool()
async def multiply(a: float, b: float) -> float:
    """Return a * b."""

    return _as_number(a) * _as_number(b)


@mcp.tool()
async def divide(a: float, b: float) -> float:
    """Return a / b."""

    a = _as_number(a)
    b = _as_number(b)

    if b == 0:
        raise ValueError("Cannot divide by zero")

    return a / b


@mcp.tool()
async def power(a: float, b: float) -> float:
    """Return a raised to the power of b."""

    a = _as_number(a)
    b = _as_number(b)

    return a ** b


@mcp.tool()
async def modulus(a: float, b: float) -> float:
    """Return the remainder when a is divided by b."""

    a = _as_number(a)
    b = _as_number(b)

    if b == 0:
        raise ValueError("Cannot calculate modulus with zero")

    return a % b


if __name__ == "__main__":
    mcp.run()