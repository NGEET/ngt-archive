# NGEE Tropics Archive Releases

## v2.4.2
Hot fix release to address issue where first author being overwritten on edit

## v2.4.1
Hot fix release to addres issue with edit button loading the wrong metedata in the form.

## v2.4.0
Refactors the publication workflow

 - Issue #348 - Refactor the publication workflow
    + Adds approval date to Dataset model
    + Removes unapprove and unsubmit actions and permissions
    + Changes edit permission to allow editing at any status
      by the managed_by user or NGEE Tropics Admin
    + Updates Edit Datasets to list all dataset editable by the logged
      in users
    + Adds historical dataset functionality for tracking Dataset changes and
      allows revert to previous versions
    + Removes duplicated checking on Dataset metadata form


## v2.3.2
Minor change to user registrations notification

  - Issue #347 - New user registration email should notify user

## v2.3.1
Bug fix release

 - Issue #346 - Metrics report download headers too short

## v2.3.0
NGEE Tropics Metrics page

 - Issue #334 - Archive Metrics Page

## v2.2.3
Bug fixes

 - Issue  #341 - jquery vulnerabilities found in …/js/jquery-2.1.4.min.js
 - Issue  #339 - Warning in logs for Django ORM models

## v2.2.2
Enables more robust error handling of data upload.

 - Issue #340 - Error Uploading 1.7 GB file

## v2.2.1
Allow admins to change who can manage data sets

 - Issue #338 


## v2.2.0
Enable collection of ORCiD for People in the database. Also,
improves handling of errors in Dataset edit form. 

Enables collection of ORCiD for Person records.
    - Enables orcid management in API and UI
    - Enhances Person Admin UI
         + download csv of all Person records
         + batch update orcids for Person records via uploaded csv


+ Implements #337 - Collect ORCiDs for Users
+ Fixes #59 - Dataset UI does not handle HTTP 500 errors

## v2.1.0
Usability and bug fixes as well as an enhancement that enables
programmatic access to the archive web service API using 
Oauth2 tokens.

+ Issue #332 - "Methods Description" is not showing on the landing page, only a colon.
+ Issue #318 - ./manage.py uploadarchive appends date twice
+ Issue #335 - Enable OAuth2 for programmatic access
+ Issue #329 - Change methods field label & description
+ Issue #333 - References on landing page
