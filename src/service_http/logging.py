
import inspect
import json
import os

from werkzeug.local import LocalProxy

def structured_log(request: LocalProxy, severity: str = 'NOTICE', message: str = None):


    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])

    # Build structured log messages as an object.
    global_log_fields = {}

    if PROJECT := os.environ.get('GOOGLE_CLOUD_PROJECT'):
    # Add log correlation to nest all log messages.
        trace_header = request.headers.get("X-Cloud-Trace-Context")

        if trace_header and PROJECT:
            trace = trace_header.split("/")
            global_log_fields[
                "logging.googleapis.com/trace"
            ] = f"projects/{PROJECT}/traces/{trace[0]}"

    # Complete a structured log entry.
    entry = dict(
        severity=severity,
        message=message, 
        # Log viewer accesses 'component' as jsonPayload.component'.
        component=f'{mod.__name__}.{frm.function}',
        **global_log_fields,
    )

    print(json.dumps(entry))