# NGEE Tropics Archive Service

NGEE Tropics Archive Service is a Django application. 

## Development Practices

* NGEE Tropics Archive Service will be using the [cactus model](https://barro.github.io/2016/02/a-succesful-git-branching-model-considered-harmful/) 
  of branching and code versioning in git. 
* Code development will be peformed in a forked copy of the repo. Commits will not be 
  made directly to the ngt-archive repo. Developers will submit a pull 
  request that is then merged by another team member, if another team member is available.
* Each pull request should contain only related modifications to a feature or bug fix.  
* Sensitive information (secret keys, usernames etc) and configuration data 
  (e.g database host port) should not be checked in to the repo.
* A practice of rebasing with the main repo should be used rather that merge commmits.  

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for 
development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisities

WFSFA is a Django application which requires:

* Python (>= 3.4, 3.5)
* Django (> 1.8)

###Setup Development
There is an option for virtual machine development and local machine 
development using vagrant.

#### Virtual Machine Development
These instructions assume that you have [Vagrant](#vagrant) installed.
The default setup is [Vagrant](#vagrant) with VirtualBox. If you would 
like to manually prepare you own VM look at the `Vagrantfile` in the 
root of this project.

### Create main.yml
Copy `main.copyme` as `main.yml` and put your sensitive information in 
there. If you don't know what this is, ask another developer.

### <a name="vagrant"></a>Vagrant VM Configuration
If you are using at  VirtualBox  and Vagrant a  development VM can be 
configured using vagrant.

    # installation instructions here
    git clone git@github.com:NGEET/ngt-archive.git
    cd ngt-archive

The next command will take a while because it will be configuring the 
box for the first time.

    $ vagrant up
    
Once that finishes you may login to your VM with the following command. 
The project directory is mounted into the VM at /vagrant.

    $ vagrant ssh
    $ cd /vagrant
    
The web application has been deployed to apache on your VM.
You may access the web application at http://localhost:9999

When you are done for the day, you may shut your VM down:

    $ vagrant halt
    
To delete your VM:

    $ vagrant destroy

#### Local Machine Development

Install WFSFA Broker Service for development

Clone the project from Github

```
git clone git@github.com:NGEET/ngt-archive.git
cd ngt-archive
```

Prepare a Python virtual environment

```
virtualenv .env  OR virtualenv -p python3 .env
source .env/bin/activate
```

Install ngt-archive for development
```
python setup.py develop
```

Create the database and load some data

```
./manage.py migrate
./manage.py createsuperuser
```

Load Test Users *superadmin, admin, auser*. Passwords are 
*ngeet2016, ngeetdata, ngeetdata* respectively.

```
./manage.py loaddata test_auth.json 
```

Load Archive Service Test Data
```
./manage.py loaddata test_archive_api.json 
```

Run a develeop server

```
./manage.py runserver  0.0.0.0:8888
Performing system checks...

System check identified no issues (0 silenced).
August 05, 2016 - 23:48:34
Django version 1.9.8, using settings 'wfsfa_broker.settings'
Starting development server at http://127.0.0.1:8888/
Quit the server with CONTROL-C.
```
**OR** use the *ngt_archive* service on ubuntu. This
service starts up at http://0.0.0.0:9999

```
sudo initctl start ngt_archive
sudo initctl stop ngt_archive
sudo initctl list | grep ngt_archive
```


## Running the tests

Automated tests are run using `manage.py`:

```
./manage.py test
```

## Deployment

Deployment notes to come.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, 
see the [tags on this repository](https://github.com/NGEET/ngt-archive/tags). 

## Authors

* **Charuleka Varadharajan** - [LBL](http://eesa.lbl.gov/profiles/charuleka-varadharajan/)
* **Valerie Hendrix**  - [LBL](https://dst.lbl.gov/people.php?p=ValHendrix)
* **Megha Sandesh**  - [LBL](https://dst.lbl.gov/people.php?p=MeghaSandesh)

See also the list of [contributors](https://github.com/NGEET/ngt-archive/contributors) who participated in this project.

## License

This project is licensed under ... - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

TBD
