def run(code: str):
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        return local_vars
    except Exception as e:
        return f"Execution error: {str(e)}"
