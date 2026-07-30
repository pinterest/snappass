import os
import typing

from flask import (
    abort, Flask, render_template, request, jsonify, make_response,
    Response, Request
)
from urllib.parse import quote_plus, unquote_plus, urljoin, urlsplit
from snappass.storage import (
    check_redis_alive,
    get_password,
    password_exists,
    set_password,
)
# _ is required to get the Jinja templates translated
from flask_babel import Babel, _  # type: ignore # noqa: F401

_no_ssl_env = os.environ.get('NO_SSL', 'False').lower()
NO_SSL: bool = _no_ssl_env in ('true', '1', 't', 'y', 'yes')
URL_PREFIX: typing.Optional[str] = os.environ.get('URL_PREFIX', None)
HOST_OVERRIDE: typing.Optional[str] = os.environ.get('HOST_OVERRIDE', None)

# Initialize Flask Application
app = Flask(__name__)
if os.environ.get('DEBUG'):
    app.debug = True
secret_key = os.environ.get('SECRET_KEY')
if not secret_key or not secret_key.strip('"\' '):
    raise ValueError(
        "Error: SECRET_KEY environment variable is not set. "
        "It is required for securely signing session cookies."
    )
app.secret_key = secret_key
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024
app.config.update(
    dict(STATIC_URL=os.environ.get('STATIC_URL', 'static')))


# Set up Babel
def get_locale() -> typing.Optional[str]:
    return request.accept_languages.best_match(['en', 'es', 'de', 'nl', 'fr'])


babel = Babel(app, locale_selector=get_locale)


TIME_CONVERSION: typing.Dict[str, int] = {
    'two weeks': 1209600,
    'week': 604800,
    'day': 86400,
    'hour': 3600
}
DEFAULT_API_TTL: int = 1209600
MAX_TTL: int = DEFAULT_API_TTL


def _request_has_trusted_host(req: Request) -> bool:
    # When HOST_OVERRIDE is not configured the base URL is derived from the
    # request's Host header, which a client can spoof. Only loopback hosts are
    # trusted for that fallback (local/dev use); production should set
    # HOST_OVERRIDE to its canonical hostname.
    parsed = urlsplit(f'//{req.host}')
    hostname = parsed.hostname
    if not hostname:
        return False
    normalized_hostname = hostname.lower().rstrip('.')
    return normalized_hostname in {'localhost', '127.0.0.1', '::1'}


def as_validation_problem(
    req: Request,
    problem_type: str,
    problem_title: str,
    invalid_params: typing.List[typing.Dict[str, str]]
) -> Response:
    base_url = set_base_url(req)

    problem = {
        "type": f"{base_url}{problem_type}",
        "title": problem_title,
        "invalid-params": invalid_params
    }
    return as_problem_response(problem)


def as_not_found_problem(
    req: Request,
    problem_type: str,
    problem_title: str,
    invalid_params: typing.List[typing.Dict[str, str]]
) -> Response:
    base_url = set_base_url(req)

    problem = {
        "type": f"{base_url}{problem_type}",
        "title": problem_title,
        "invalid-params": invalid_params
    }
    return as_problem_response(problem, 404)


def as_problem_response(
    problem: typing.Dict[str, typing.Any],
    status_code: typing.Optional[int] = None
) -> Response:
    if not isinstance(status_code, int) or not status_code:
        status_code = 400

    response = make_response(jsonify(problem), status_code)
    response.headers['Content-Type'] = 'application/problem+json'
    return response


def empty(value: typing.Optional[str]) -> bool:
    return not value


def set_base_url(req: Request) -> str:
    scheme = 'http' if NO_SSL else 'https'
    if HOST_OVERRIDE:
        base_url = f'{scheme}://{HOST_OVERRIDE}/'
    else:
        if not _request_has_trusted_host(req):
            abort(400)
        base_url = req.url_root
        if not NO_SSL:
            base_url = base_url.replace("http://", "https://")
    if URL_PREFIX:
        base_url = f"{base_url}{URL_PREFIX.strip('/')}/"
    return base_url


@app.route('/', methods=['GET'])
def index() -> str:
    return render_template('set_password.html')


@app.route('/', methods=['POST'])
def handle_password() -> typing.Union[Response, str, typing.Tuple[str, int]]:
    password = request.form.get('password')
    ttl = request.form.get('ttl')

    if password and len(password) > 384 * 1024:
        error_msg = _('The secret is too long. The maximum allowed size is 256kb.')
        if request.accept_mimetypes.accept_json:
            return make_response(jsonify(error=error_msg), 400)
        else:
            abort(400)
    if password and ttl and not empty(password) and not empty(ttl):
        ttl_val = TIME_CONVERSION.get(ttl.lower())
        if not ttl_val:
            abort(400)
        token = set_password(password, ttl_val)
        base_url = set_base_url(request)
        link = f"{base_url}{quote_plus(token)}"

        # We merge confirm.html into set_password.html via AJAX,
        # so this endpoint should always return JSON for clients using AJAX.
        if request.accept_mimetypes.accept_json:
            return jsonify(link=link, ttl=ttl_val)
        else:
            # Fallback if someone submits form without JS
            return render_template('confirm.html', password_link=link)
    else:
        abort(500)


@app.route('/api/set_password/', methods=['POST'])
def api_handle_password() -> Response:
    password = request.json.get('password')
    ttl = int(request.json.get('ttl', DEFAULT_API_TTL))

    if password and len(password) > 384 * 1024:
        error_msg = _('The secret is too long. The maximum allowed size is 256kb.')
        return make_response(jsonify(error=error_msg), 400)
    if password and isinstance(ttl, int) and ttl <= MAX_TTL:
        token = set_password(password, ttl)
        base_url = set_base_url(request)
        link = f"{base_url}{quote_plus(token)}"
        return jsonify(link=link, ttl=ttl)
    else:
        abort(500)


@app.route('/api/v2/passwords', methods=['POST'])
def api_v2_set_password() -> Response:
    password = request.json.get('password')
    ttl = int(request.json.get('ttl', DEFAULT_API_TTL))

    invalid_params = []

    if not password:
        invalid_params.append({
            "name": "password",
            "reason": "The password is required and must not be empty."
        })
    elif len(password) > 384 * 1024:
        invalid_params.append({
            "name": "password",
            "reason": _("The secret is too long. The maximum allowed size is 256kb.")
        })

    if not isinstance(ttl, int) or ttl > MAX_TTL:
        invalid_params.append({
            "name": "ttl",
            "reason": "The specified TTL is longer than the maximum supported."
        })

    if len(invalid_params) > 0:
        return as_validation_problem(
            request,
            "set-password-validation-error",
            "The password and/or the TTL are invalid.",
            invalid_params
        )

    token = set_password(password, ttl)
    url_token = quote_plus(token)
    base_url = set_base_url(request)
    api_link = urljoin(base_url, f"{request.path}/{url_token}")
    web_link = urljoin(base_url, url_token)

    response_content = {
        "token": token,
        "links": [{
            "rel": "self",
            "href": api_link
        }, {
            "rel": "web-view",
            "href": web_link
        }],
        "ttl": ttl
    }
    return jsonify(response_content)


@app.route('/api/v2/passwords/<token>', methods=['HEAD'])
def api_v2_check_password(token: str) -> typing.Tuple[str, int]:
    token = unquote_plus(token)
    if not password_exists(token):
        # Return NotFound, to indicate that password does not exist
        return ('', 404)
    else:
        # Return OK, to indicate that password still exists
        return ('', 200)


@app.route('/api/v2/passwords/<token>', methods=['GET'])
def api_v2_retrieve_password(token: str) -> Response:
    token = unquote_plus(token)
    password = get_password(token)
    if not password:
        # Return NotFound, to indicate that password does not exist
        return as_not_found_problem(
            request,
            "get-password-error",
            "The password doesn't exist.",
            [{"name": "token"}]
        )
    else:
        # Return OK and the password in JSON message
        return jsonify(password=password)


@app.route('/<password_key>', methods=['GET'])
def preview_password(
    password_key: str
) -> typing.Union[str, typing.Tuple[str, int]]:
    password_key = unquote_plus(password_key)
    if not password_exists(password_key):
        return render_template('expired.html'), 404

    return render_template('preview.html')


@app.route('/<password_key>', methods=['POST'])
def show_password(
    password_key: str
) -> typing.Union[str, typing.Tuple[str, int]]:
    password_key = unquote_plus(password_key)
    password = get_password(password_key)
    if not password:
        return render_template('expired.html'), 404

    return render_template('password.html', password=password)


@app.route('/_/_/health', methods=['GET'])
@check_redis_alive
def health_check() -> typing.Dict[typing.Any, typing.Any]:
    return {}


@check_redis_alive
def main() -> None:
    app.run(host=os.environ.get('SNAPPASS_BIND_ADDRESS', '0.0.0.0'),  # noqa: S104
            port=int(os.environ.get('SNAPPASS_PORT', 5000)))


if __name__ == '__main__':
    main()