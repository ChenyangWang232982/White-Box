import inspect


def get_caller_name():
    """
    Get the name of the caller function.
    
    Returns:
        str: The name of the caller function, or 'unknown' if it cannot be determined.
    """
    try:
        frame = inspect.currentframe()
        if frame is None:
            return 'unknown'
        caller_frame = frame.f_back
        if caller_frame is None:
            return 'unknown'
        return caller_frame.f_code.co_name
    finally:
        del frame  # 避免循环引用


