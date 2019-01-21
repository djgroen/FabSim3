FROM ubuntu
FROM python:3


RUN apt-get update
RUN apt-get install -y openssh-server
RUN apt-get install -y rsync

RUN git clone https://github.com/djgroen/FabSim3.git

WORKDIR $PWD/FabSim3

RUN pip install -r requirements.txt
RUN pip install numpy
RUN sed "s/your-username/`whoami`/g;s#~/Codes/FabSim#$PWD/FabSim3#g"  << cat deploy/machines_user_example.yml > deploy/machines_user.yml
RUN rm -f ~/.ssh/id_rsa
RUN ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
RUN cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
RUN chmod og-wx ~/.ssh/authorized_keys
RUN fab localhost install_plugin:FabDummy

ENTRYPOINT service ssh restart && bash
