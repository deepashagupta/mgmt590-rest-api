FROM pytorch/pytorch

FROM tensorflow/tensorflow

COPY requirements.txt . 

RUN pip install -r requirements.txt 

COPY answer.py .

CMD ["python3", "answer.py"]
