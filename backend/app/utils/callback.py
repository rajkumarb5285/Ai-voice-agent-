import contextvars

# ContextVar to hold the streaming callback securely across async task boundaries.
# The value is a coroutine function: async def callback(token: str) -> None:
token_callback_var = contextvars.ContextVar("token_callback", default=None)
