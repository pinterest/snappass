FROM python:3.14-slim-trixie

ENV APP_DIR=/usr/src/snappass

RUN groupadd -r snappass && \
    useradd -r -g snappass snappass && \
    mkdir -p $APP_DIR

WORKDIR $APP_DIR

COPY ["pyproject.toml", "README.rst", "AUTHORS.rst", "LICENSE", "$APP_DIR/"]
COPY ["./snappass", "$APP_DIR/snappass"]

RUN pip install --no-cache-dir . && \
    pybabel compile -d snappass/translations && \
    pip install --no-cache-dir . && \
    chown -R snappass $APP_DIR && \
    chgrp -R snappass $APP_DIR

USER snappass

# Default Flask port
EXPOSE 5000

CMD ["snappass"]
