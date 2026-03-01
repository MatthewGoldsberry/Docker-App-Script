FROM python:3.14-alpine

# set working directory
WORKDIR /home

# copy necessary files into the image
COPY data/ /home/data
COPY script.py .

# automatically execute the python script 
CMD ["python", "-m", "script"]