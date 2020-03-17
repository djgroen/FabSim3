FROM alpine:3.9 AS QCG_base_image

# define arguments
ARG SVN=https://apps.man.poznan.pl/svn/qcg-broker/branches/vecma/
ARG SVN_USER=piontek
ARG SVN_PASSWD=piontek

# install tools needs to build qcg-client
RUN set -x \
    && apk add --no-cache apache-ant openjdk8 subversion \
    && rm -rf /var/cache/apk/*

# download, build, deploy qcg-client
RUN mkdir -p QCG && \
   svn co --username ${SVN_USER} --password ${SVN_PASSWD} --non-interactive ${SVN} /QCG/source && \
   ant -f /QCG/source/build.xml client-rebuild && \
   rm -r -f /QCG/build && \
   ant -f /QCG/source/build.xml -Ddeploy.dir=/QCG/build deploy-client-single-dir && \
   sed -i -e "s/\`hostname\`/qcg.man.poznan.pl/" /QCG/build/etc/qcg-broker-client.conf && \
   sed -i -e "s#agave7.man.poznan.pl:8443/qcg/services/#broker.plgrid.qcg.psnc.pl:8443/qcg/services/#g" /QCG/build/etc/qcg-broker-client.conf && \
   sed -i -e "s#qcg-broker.man.poznan.pl#broker.plgrid.qcg.psnc.pl#g" /QCG/build/etc/qcg-broker-client.conf && \
   rm -r -f /QCG/source


FROM ubuntu:latest

COPY --from=QCG_base_image /QCG /QCG


RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo git wget gnupg python3-pip python3-dev openssh-server rsync openjdk-8-jdk nano systemd && \
    wget -q -O - https://dist.eugridpma.info/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 | apt-key add - && \
    echo "#### EGI Trust Anchor Distribution ####" >> /etc/apt/sources.list && \
    echo "deb http://repository.egi.eu/sw/production/cas/1/current egi-igtf core" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y ca-policy-egi-core && \
    apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/

RUN cd /usr/local/bin \
    && ln -s /usr/bin/python3 python \
    && pip3 install --upgrade pip \
    && pip install -U pip setuptools \
    && pip install pyyaml numpy fabric3 cryptography==2.4.2 
    # && pip install easyvvuq muscle3



ENV PATH="/QCG/build/bin:${PATH}"

RUN mkdir -p /FabSim3 && \
    chmod -R a+rwX /FabSim3 && \
    mkdir ~/.globus
WORKDIR /FabSim3
RUN echo \
"usercert=/FabSim3/.globus/usercert.pem \n\
userkey=/FabSim3/.globus/userkey.pem \n\
proxy=/FabSim3/.globus/proxy" > ~/.globus/cog.properties

RUN mkdir /var/run/sshd && mkdir ~/.ssh
RUN echo 'root:root' | chpasswd
RUN sed -i 's/#PermitRootLogin .*$/PermitRootLogin yes/' /etc/ssh/sshd_config

RUN sed -i -e 's/#force_color_prompt=yes$/force_color_prompt=yes/'  /root/.bashrc
RUN echo 'export PS1="\[\033[01;32m\]\h\[\033[00m\][\[\033[02;33m\]\D{%F}\[\033[08m\]T\[\033[00m\]\[\033[01;35m\]\D{%T}\[\033[00m\]]\[\033[01;34m\]\w\[\033[00m\]\$ "' >> /root/.bashrc
RUN echo 'PROMPT_COMMAND+=$'\n'"chmod -R a+rwX /FabSim3"' >> /root/.bashrc

ENTRYPOINT  service ssh restart && /bin/bash
