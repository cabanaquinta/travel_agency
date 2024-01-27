FROM prefecthq/prefect:2.6.5-python3.10
# Set the working directory inside the container
WORKDIR /app
# Copy the local Python files into the container's working directory
COPY ./prefect /app/
RUN ["pip", "install", "gcsfs", "numpy", "pandas", "scrapy", "pandas-gbq", "prefect-gcp[cloud_storage]", "unidecode"]

CMD prefect agent start -p my-cloud-run-pool



# docker build -t europe-west6-docker.pkg.dev/amazing-thought-394210/test/latest-image-9:2.6.5-python3.10 .
# docker push europe-west6-docker.pkg.dev/amazing-thought-394210/test/latest-image-9:2.6.5-python3.10
