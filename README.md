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
* Platform (Mac, Linux)

###Setup Development
There is an option for  local machine 
development and virtual machine development using vagrant.

#### Desktop
Use these instructions for setting up development on a desktop computer.

Fork the repository and then clone your fork:

    # installation instructions here
    git clone git@github.com:<your username here>/ngt-archive.git
    cd ngt-archive

Create a virtual environment for development
    
    virtualenv -p /Library/Frameworks/Python.framework/Versions/3.4/bin/python3.4 .menv
    source .menv/bin/activate
    
Install the a django project for development
    
    python setup.py develop
    ./manage.py collectstatic
    ./manage.py migrate
    ./manage.py loaddata test_auth.json test_archive_api.json
    
    
Run the development server. Test users/passes are: `superadmin/ngeet2016`, `admin/ngeetdata`,
`auser/ngeetdata`.

    ./manage.py runserver

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
    $ sudo ansible-playbook vagrant.yml
    
The web application has been deployed to apache on your VM.
Use the *ngt_archive* service on ubuntu. This
service starts up at http://0.0.0.0:9999

```
sudo initctl start ngt_archive
sudo initctl stop ngt_archive
sudo initctl list | grep ngt_archive
```

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

Run a develop server

```
./manage.py runserver  0.0.0.0:8888
Performing system checks...

System check identified no issues (0 silenced).
August 05, 2016 - 23:48:34
Django version 1.9.8, using settings 'wfsfa_broker.settings'
Starting development server at http://127.0.0.1:8888/
Quit the server with CONTROL-C.
```


## Running the tests

Automated tests are run using `manage.py`:

```
./manage.py test
```

## Deployment
Guidelines for preparing the application for deployment.
Database and operating system are up to the user.

Prepare django application distribution for deployment.

    $ python setup.py sdist
    Writing ngt_archive-<version>/setup.cfg
    Creating tar archive
    removing 'ngt_archive-<version>' (and everything under it)

Create deployment directory with a Python 3 virtual environment

    $ mkdir <deploy_dir>
    $ cd <deploy_dir>
    $ virtualenv -p python3 .
    
Install NGT Archive service and its dependencies.

    $ <deploy_dir>/bin/pip install ngt_archive-<version>.tar.gz
    $ <deploy_dir>/bin/pip install psycopg2 (For Postgres DB)
    
Link to the Django applications `manange.py` script

    $ cd <deploy_dir>
    $ ln -s lib/python3.4/site-packages/manage.py manage.py
    
Create custom Django settings in `<deploy_dir>/settings/local.py`. Use
[settings_local_py.jinja2](settings_local_py.jinja2) as an example. Replace
template variables in curly braces with your configuration.

Initialize the application

    $ <deploy_dir>/manage.py migrate
    $ <deploy_dir>/manage.py collectstatic
    

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, 
see the [tags on this repository](https://github.com/NGEET/ngt-archive/tags). 

Workflow for tagging and building release:

1. checkout the version to tag from `master`
1. `git -a v[version]-[release] -m "Tagging release v[version]-[release]"`
1. build distribution with `setup.py`
1. `git push origin v[version]-[release]`

## Authors

* **Charuleka Varadharajan** - [LBL](http://eesa.lbl.gov/profiles/charuleka-varadharajan/)
* **Valerie Hendrix**  - [LBL](https://dst.lbl.gov/people.php?p=ValHendrix)
* **Megha Sandesh**  - [LBL](https://dst.lbl.gov/people.php?p=MeghaSandesh)

See also the list of [contributors](https://github.com/NGEET/ngt-archive/contributors) who participated in this project.

## License

See [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

TBD
