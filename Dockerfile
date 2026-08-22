FROM python:3.12-slim

ENV APP_DIR=/usr/src/snappass

RUN groupadd -r snappass && \
    useradd -r -g snappass snappass && \
    mkdir -p $APP_DIR

WORKDIR $APP_DIR

COPY ["setup.py", "requirements.txt", "MANIFEST.in", "README.rst", "AUTHORS.rst", "$APP_DIR/"]
COPY ["./snappass", "$APP_DIR/snappass"]

# setuptools is required for setup.py install on modern Python slim images
RUN pip install --no-cache-dir -r requirements.txt setuptools wheel && \
    pybabel compile -d snappass/translations && \
    python setup.py install && \
    chown -R snappass $APP_DIR && \
    chgrp -R snappass $APP_DIR

USER snappass

# Default Flask port
EXPOSE 5000

CMD ["snappass"]
