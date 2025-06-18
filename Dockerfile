FROM python:3.12-slim

WORKDIR /opt/shared

COPY . .

RUN pip install .

RUN chmod a+x ./scripts/download-apk.sh && \
    ./scripts/download-apk.sh

VOLUME ["/opt/shared/eval_results"]

ENTRYPOINT ["droidrun-android-world"]
