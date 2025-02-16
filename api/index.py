from backend.app import app  # Import your existing Flask app


def handler(request, response):
    """
    A simple WSGI adapter to allow your Flask app to run as a Vercel serverless function.
    """
    # Convert Vercel's request/response objects to a WSGI-compatible format
    environ = request.environ
    # Define a start_response function that Vercel's response object expects

    def start_response(status, headers):
        response.status_code = int(status.split(" ")[0])
        for header, value in headers:
            response.headers[header] = value
    return app(environ, start_response)
