FROM alpine:3

WORKDIR /opt/pretenders
ENV PYTHONPATH=/opt/pretenders
EXPOSE 8000

COPY requirements/ requirements/

RUN apk --no-cache add \
        bash \
        python3 \
        py3-pip \
    && \
    pip install -r /opt/pretenders/requirements/runtime.txt

COPY pretenders/ pretenders/

CMD ["python3", "-m", "pretenders.server.server", "--host", "0.0.0.0", "--port", "8000"]
