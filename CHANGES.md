# NGEE Tropics Archive Releases

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
