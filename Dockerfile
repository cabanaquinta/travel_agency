FROM prefecthq/prefect:2.6.5-python3.10
# Set the working directory inside the container
WORKDIR /app
# Copy the local Python files into the container's working directory
COPY ./prefect/tasks/prefect_tasks.py /app/tasks/prefect_tasks.py
RUN ["pip", "install", "gcsfs", "numpy", "pandas", "scrapy", "pandas-gbq", "prefect-gcp[cloud_storage]", "unidecode"]

CMD prefect agent start -p my-cloud-run-pool
