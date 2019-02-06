#### Before install QCG-Client via `qcg_client_installer.sh` please make sure all required packages are installed on your local machine.


### Install server certificates
The following procedure was tested in Ubuntu machines. For other linux distributions or extra information, please refer to [EGI IGTF Release](https://wiki.egi.eu/wiki/EGI_IGTF_Release)
- Install the [EUGridPMA](https://www.eugridpma.org/) PGP key as root (```$ su```):
    ```sh
    $ wget -q -O - https://dist.eugridpma.info/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 | apt-key add -
    ```
- Add the following line to your sources.list file for APT: 
    ```sh
    $ echo "#### EGI Trust Anchor Distribution ####" >> /etc/apt/sources.list
    $ echo "deb http://repository.egi.eu/sw/production/cas/1/current egi-igtf core" >> /etc/apt/sources.list
    ```
- Update and install the meta-package
    ```sh
    $ apt-get update
    $ apt-get install ca-policy-egi-core
    ```
### Install Subversion package
- Install latest available Subversion package using
    ```sh
    $ sudo apt-get install subversion
    ```
### Install apache ant
- Install Apache Ant using
    ```sh
    $ sudo apt-get install ant
    ```

### Install Java Version 8
- first check if you already installed or not
    ```sh
    $ sudo update-alternatives --config java
    ``` 
- if NOT, follow these commands
    ```sh
    $ sudo add-apt-repository ppa:webupd8team/java
    $ sudo apt-get update
    $ sudo apt-get install oracle-java8-installer
    ``` 
