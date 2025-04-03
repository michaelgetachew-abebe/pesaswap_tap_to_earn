FROM python:3.9

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV ZEP_API_KEY="z_1dWlkIjoiN2E2NGU4ZjQtNTU1MS00ZWVjLTg4NDctMTU4NWQ0NTBiMjQ3In0.N71r_knGeIVOnsHQLWj2utUTpA5iBYqPtYADTLh0I37qlU85odLvzjhjMLU0RE5m4YI6Fe7_1ln-BnJsb6iUPQ"

COPY . .

EXPOSE ${BACKEND_PORT:-8000}

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8000}"]

# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]