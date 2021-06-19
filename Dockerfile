FROM python:3.7.4-stretch

# setup poetry
RUN pip install "poetry==1.1.6"

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY models/ /app/models/
COPY poetry.lock pyproject.toml /app/
COPY .streamlit/ /app/.streamlit
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY src/ /app/src/
COPY app.py /app/app.py

RUN mkdir -p /root/.streamlit
RUN bash -c 'echo -e "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > /root/.streamlit/credentials.toml'

EXPOSE 8501
CMD ["streamlit", "run", "/app/app.py"]
