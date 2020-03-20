# NGEE Tropics Archive Service

NGEE Tropics Archive Service is a Django application.  The NGEE-Tropics archive 
service sits in the middle of the *NGEE Tropics data workflow*

* Place to upload datasets and metadata.
* Datasets should consist of related data collections, not individual files (e.g. Sapflow collected at Manaus)
* Datasets will receive a DOI, and can be updated with new data.
* Datasets will be available for search to NGEE Tropics team, and (if policy allows) to public
* Makes NGEE-Tropics compliant with DOE Data Management Plan


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

NGEE Tropics Archive is a Django application which requires:

* Python ( >= 3.6)
* Django ( >= 3.0.5 )
* Platform (Mac, Linux)

### Setup Development
There is an option for  local machine 
development.

#### Desktop
Use these instructions for setting up development on a desktop computer.

Fork the repository and then clone your fork:

    # installation instructions here
    git clone git@github.com:<your username here>/ngt-archive.git
    cd ngt-archive

Create a virtual environment for development
    
    # Python verion >= 3.6
    python -m venv .menv
    source .menv/bin/activate
    
Install the a django project for development
    
    python setup.py develop
    ./manage.py collectstatic
    ./manage.py migrate
    ./manage.py loaddata test_auth.json test_archive_api.json
    
    
Run the development server. Test users/passes are: `superadmin/ngeet2016`, `admin/ngeetdata`,
`auser/ngeetdata`.

    ./manage.py runserver

#### Docker Container Setup
These instructions assume that you have [Docker](#docker) installed. 

### Create environment file
Copy `env.copyme` as `.env` and put your sensitive information in 
there. If you don't know what this is, ask another developer.

### <a name="docker"></a>Docker Configuration
To execute NGEE Tropics on docker.  Follow the steps below.

    # installation instructions here
    git clone git@github.com:NGEET/ngt-archive.git
    cd ngt-archive

The next command will take a while because it will be configuring the 
box for the first time.

    $ docker-compose up -d
    $ docker-compose exec app ./manage.py loaddata archive_api/fixtures/test_auth.json archive_api/fixtures/test_archive_api.json

Load Test Users *superadmin, admin, auser*. Passwords are 
*ngeet2016, ngeetdata, ngeetdata* respectively.
    
The web application has been deployed to apache on your container.
This service starts up at http://0.0.0.0:8088



When you are done for the day, you may stop container down:

    $ docker-compose stop
    
To delete your stack:

    $ docker-compose rm -fs

#### Local Machine Development

Install NGEE Tropics Archive Service for development

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
1. `git tag -a v[version]-[release] -m "Tagging release v[version]-[release]"`
1. build distribution with `setup.py`
1. `git push origin v[version]-[release]`

## Authors

* **Charuleka Varadharajan** - [LBL](http://eesa.lbl.gov/profiles/charuleka-varadharajan/)
* **Valerie Hendrix**  - [LBL](https://dst.lbl.gov/people.php?p=ValHendrix)
* **Megha Sandesh**  - [LBL]
* **Deb Agarwal**  - [LBL](https://dst.lbl.gov/people.php?p=DebAgarwal)

See also the list of [contributors](https://github.com/NGEET/ngt-archive/contributors) who participated in this project.

## License

See [LICENSE.md](LICENSE.md) file for details

## Copyright Notice

NGEE Tropics Archive (NGT Archive) Copyright (c) 2017, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy).  All rights reserved.
 
If you have questions about your rights to use or distribute this software, please contact Berkeley Lab's Innovation & Partnerships Office at  IPO@lbl.gov.
 
NOTICE.  This Software was developed under funding from the U.S. Department of Energy and the U.S. Government consequently retains certain rights. As such, the U.S. Government has been granted for itself and others acting on its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software to reproduce, distribute copies to the public, prepare derivative works, and perform publicly and display publicly, and to permit other to do so. 
