#Initialise the python image
FROM python:3.12-slim

#Install uv using pip
RUN pip install --no-cache-dir uv

#Set the working directory in the container
WORKDIR /app

#copy only the dependency files first. docker caches this layer and only
#rebuilds it when the lockfile changes, so editing an agent does not reinstall
#langchain and pandas every time.
COPY pyproject.toml uv.lock ./

#install from uv.lock, which is what the project already uses locally, instead
#of a second hand written requirements.txt that drifts out of sync.
#--frozen installs exactly what the lockfile pins and errors out rather than
#quietly resolving new versions, --no-dev keeps pytest out of the image, and
#--no-install-project because the app runs from the source copied below rather
#than being installed as a package.
RUN uv sync --frozen --no-install-project --no-dev

#uv put the venv in /app/.venv. putting it on PATH means `streamlit` and
#`python` resolve to it, so the CMD below does not need `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

#Copy the entire project in the working directory
COPY . .

#expose the port. 8501 is streamlit's default, not 8000 - this project serves a
#streamlit app, there is no asgi app to hand to uvicorn.
EXPOSE 8501

#--server.address 0.0.0.0 so the port is reachable from outside the container,
#and --server.headless so streamlit does not try to open a browser that does
#not exist in here.
CMD ["streamlit", "run", "ui/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
