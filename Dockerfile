FROM python:3

ARG installdir=/usr/src/RancherProjectManager/
RUN mkdir $installdir
COPY ./main.py $installdir
COPY ./RancherProjectManager $installdir/RancherProjectManager
WORKDIR $installdir

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

RUN chmod +x ./main.py
ENTRYPOINT "./main.py"