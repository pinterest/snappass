FROM python:3.7.2-slim

ARG APP_DIR=/usr/src/snappass

RUN groupadd -r snappass && \
    useradd -r -g snappass snappass && \
    mkdir -p $APP_DIR

WORKDIR $APP_DIR

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./snappass $APP_DIR

RUN chown -R snappass $APP_DIR && \
    chgrp -R snappass $APP_DIR

USER snappass

# Default Flask port
EXPOSE 5000


CMD ["python3.7", "/usr/src/snappass", "5000"]
