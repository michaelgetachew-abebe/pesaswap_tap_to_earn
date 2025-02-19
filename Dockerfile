FROM python:3.11

WORKDIR /app

RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org python_telegram_bot~=20.0a4
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org python-dotenv~=0.21.0

COPY . .

EXPOSE 8080

CMD ["python", "app.py"]