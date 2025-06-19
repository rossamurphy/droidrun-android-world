FROM python:3.12-slim

WORKDIR /opt/shared

# download droidrun portal apk
COPY ./scripts/download-apk.sh ./scripts/download-apk.sh
RUN apt-get update && \
    apt-get install -y curl adb && \
    chmod a+x ./scripts/download-apk.sh && \
    ./scripts/download-apk.sh

# install droidrun-android-world cli
COPY . .
RUN --mount=type=cache,target=/root/.cache/pip pip install .

VOLUME ["/opt/shared/eval_results"]

ENTRYPOINT ["droidrun-android-world"]
