FROM ubuntu:latest

RUN apt-get update && \
	apt-get install -y git python3-pip python3-dev openssh-server rsync

RUN cd /usr/local/bin \
	&& ln -s /usr/bin/python3 python \
	&& pip3 install --upgrade pip

RUN git clone https://github.com/djgroen/FabSim3.git

WORKDIR $PWD/FabSim3

RUN pip install -r requirements.txt
RUN pip install numpy
RUN sed "s/your-username/`whoami`/g;s#~/Codes/FabSim#$PWD#g"  << cat deploy/machines_user_example.yml > deploy/machines_user.yml
RUN rm -f ~/.ssh/id_rsa
RUN ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
RUN cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
RUN chmod og-wx ~/.ssh/authorized_keys
RUN fab localhost install_plugin:FabDummy

ENTRYPOINT service ssh restart && bash
