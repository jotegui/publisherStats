Usage Report Generation
=======================

A VertNet tool for creating and delivering Data Usage Reports.
Author: Javier Otegui.

Requirements
------------

In order to work, the following python modules must be installed and available:
* logging
* pickle
* requests
* base64
* jinja2

Besides, GitHub API requires an authentication token for the VertNet-related repositories. This token (a string of numbers and letters) must be stored in the same folder as the utils.py module, and must be named 'VN.key'. For security reasons, I am not uploading it to the repository.

See more about this:
https://developer.github.com/v3/oauth/
https://developer.github.com/v3/oauth_authorizations/#create-a-new-authorization

Installation
------------

Simply clone the repository to a local folder with the git clone command.

What it does
------------

Let's assume a complete run, no testing and no beta-testing.

The launch.py script configures the logging and launching variables, and launches the main process from the monthlyStatReports module.

The main function executes sequentially all the other steps. This function calls different sub-functions depending on the launching variable configuration (like if it is a test run, or if counts are taken from a local file -- see 'modes'). There are 4 main steps:

1. Extract the usage stats
2. Generate the reports
3. Upload the reports and models to GitHub
4. Create issues for each uploaded report

The code for each step is in a different file and has a 'main' function that performs the required steps sequentially.


# Extract the usage stats

The first part of the process itself is the extraction of usage stats for the past month. All the code related to this part of the process is in the extractStats.py module.

First, it gets information on all download events from CartoDB, with the get_cdb_downloads function. This function performs the following query on CartoDB API

    select * from query_log where download is not null and download !='' and client='portal-prod'

adding the time window (the previous month) with the add_time_limit function, from the same module, which adds the following (assuming the process is run on september):

    and extract(year from created_at)=2014 and extract(month from created_at)=8

Then, for each download event, extracts the location of the download file in Google Cloud Storage, from the 'download' field in the CartoDB download event. This is performed by the get_file_list function, which returns a list with Cloud Storage URIs (gs://vertnet-downloads/...)

The next function get_gcs_counts downloads each file from the list and prepares some counts. It creates a dictionary of resources (named 'pubs') where all the counts for all resources will be stored. Let's see the process it follows for each file in the file list.

* First, it tries to download the file itself. A query might fail for big downloads or randomly, so it might be possible that the file cannot be found. In that case, it will throw a warning to the logs and continue with the next file.
* If the file is found, the headers are removed, and the processing of each record begins
* The institutioncode, collectioncode and source URL are extracted from the record, and some sanity checks are performed (like changing "Royal Ontario Museum" for "ROM", or changing some URLs, see sanity_check function in util.py). Collectioncode is taken from the URL, with the value after the "=" sign. If the record does not have institutioncode, it tries to extract the institutioncode and collectioncode values from the URL by calling the resource_staging table in CartoDB. If it still cannot find them, it will skip the record. Otherwise, the union of institutioncode and collectioncode will be used as an internal identifier (_e.g._, "MVZ-mvz_herp").
* Then, a pseudo-unique identifier is built to calculate counts on unique record downloads.
* If this resource is not yet in the 'pubs' dictionary, it will create a pseudo-model for it. This pseudo-model has the following elements:
  * Metadata: url, inst, col.
  * download_files: a list of all the files in which this resource is present. This will later be collapsed into a single number.
  * records_downloaded and downloads_in_period: a count of how many times a particular record from this resource has been downloaded and how many times any record from this resource has been downloaded.
  * unique_records: a set of all the pseudo-unique identifiers. This will later be collapsed into a single number.
  * Dictionaries for storing download variables: from where (latlon), when (created) and with which terms (query).
* If the resource already exists, it will add 1 to the records_downloaded and append the file name to the download_files.

And that ends the counts on the Cloud Storage file. The next step is to store the location, date and query terms associated with each download. This is accomplished by the match_gcs_cdb function. For each of the resources in 'pubs', it will find the corresponding download event from the CartoDB download events and will populate the latlon, created and query elements of the pseudo-model, as defined in function get_cdb_stats.

As the last step of the extraction of stats, it will get some counts on searches. So far, this has been only to deal with downloads. The count of searches is handled by the get_cdb_searches function and it creates another pseudo-model with number of search events, number of records searched and metadata on the resource. The last piece of the module deals with the integration between downloads and searches, adding searches as a sub-model of each pseudo-model in the general 'pubs' dictionary.

Then, extractStats.py returns the 'pubs' dictionary, with the counts for each resource.


# (Optional) Store the 'pubs' object

If the process is launched with the "to_local" flag, the 'pubs' dictionary will be stored in disk as a pickle object. This avoids having to download again the files and calculate the counts if something goes wrong in the rest of the steps.


# Generate the reports

The second part of the process deals with the generation of the reports, the texts that will be sent to the GitHub repositories. All the code related to this part of the process is in the generateReports.py module.

In this section, a proper model is built for each resource. This module has three main steps:

1. Build the model with the data for the month
2. Add past and cumulative data to the model
3. Generate the report itself

## Build the model

The model skeleton can be found in the build_model function. The rest of the function assigns each value from the pseudo-model in 'pubs' to the corresponding place in the model. The code might look a bit overwhelming, but this is actually one of the simplest parts of the process. There is however a key step here, which is locating the last existing report for that resource. This is done by the find_last_report function. This function opens a file that contains the URLs for all the models, finds the list of available models for the given resource and retrieves the last one. This value is stored in the last_report_url field of the model.

## Add past and cumulative data

The second step is trickier, and it involves loading the last existing report and adding the values to the current model, and adding the current model values to the year and history cumulative counts.

Loading and adding the last existing report is done by the load_previous_model function. In the beginning, there was no previous model available, so the legacy data had to be taken from special functions, called add_initial_year and add_initial_history. Nowadays, it is difficult to believe that a resource has not been searched or downloaded even once, so the section if last_report_url is empty should not be executed. The second part of the function takes the actual stored model, referenced by last_report_url, and populates the 'year' and 'history' sections of the model with the data in the last report. In case grabbing the last available model fails for any reason, it will make up to 5 attempts, each one logged with a warning message. In order to avoid further problems, if the function is unable to find the last model, it will fill the 'year' and 'history' sections of the current model with 0s.

Then, the add_history_year_data function takes the counts from the current month and adds them to the yearly and historical counts. This function resets the counts for the year if the report is for January, and otherwise, it runs twice: once for adding the month's counts to the 'year' section and once for adding the month's counts to the 'history' section.

## Generate the report itself

The last big function in this module is the create_report. This function uses the jinja2 module to dynamically fill two templates, an html file and a txt file, with the proper values.

There is a special function here, called countries_dates_queries, that generates the final version of the counts for the breakdown by country, date and query terms. Then, placeholders are created for each value that is missing. Finally, the two templates are filled with the adequate data. Both templates are provided in the package, and are called template.txt and template.html. The function returns the strings for both files.

Then, generateReports.py returns the models (JSON-like structured counts) in 'models' and the reports (templates with values filled, rendered as strings) in 'reports'.


# Upload the reports and models to GitHub

The third part of the process deals with uploading the reports and models to GitHub. The reports will be uploaded to the repository of the resource it relates to, and the models will be uploaded to a VertNet administrative repository. Currently, it is being uploaded to one of my personal repositories, but that will change with the actual final version. All the code related to this part of the process is in the uploadToGithub.py module.

This process is divided into two steps: uploading the reports and uploading the models. If the script is run in beta-testing mode, a first function called beta_testing will shrink the list of resources, leaving only those belonging to beta-testing organizations.

## Upload of the reports

The function that deals with this step is called put_store_reports. This function is a wrapper for putting the reports in GitHub and storing them in the local file system, in JSON format. The code that puts the reports in GitHub is under the put_all function.

First, a list with all resources is created, in pubs_to_check = reports.keys() (line 38). All the successfully finished resources will be popped from this list, and in the end only those that failed will remain. Then, the function iterates over the list of resources.

For each resource, the function calls the get_org_repo function to extract the name of the GitHub organization and repository, and then calls the put_report function with those variables and the reports.

The put_report function is the one that uploads the reports to the resources' repositories. It first populates all the needed variables and then launches the PUT request. The request (line 107) needs 3 elements:

* The URL of the request. In our case, the URL takes the form of https://api.github.com/repos/{0}/{1}/contents/{2}, where {0} is the organization, {1} is the repository and {2} is the path to the file within the repository
* A 'data' parameter, with a JSON object that contains three elements: (1) a message, in our case somthing like "Usage report for 2014/08), (2) a commiter, in our case {'name': 'VertNet', 'email': 'vertnetinfo@vertnet.org'}, and (3) the content to upload, in our case the text of the report. The content must be base64 encoded in order to be accepted by GitHub.
* A 'headers' parameter, basically with authentication. The 'headers' paramenter must have a 'User-Agent' element, in our case 'VertNet', and an authorization token. If the process is run intesting mode, the token will allow uploading to the testing repository (currently, one of my personal repos); otherwise, it will allow uploading the reports to any organization VertNet has access to.

If the PUT request is successful, the function will return two values: the url of the git object and the SHA. Both are required for further accessing the object via API, and they will later be stored in an administrative repository.

Sometimes, the process might fail in the middle of uploading the reports and it has to be launched again. For those cases, the function is ready to handle the case that the report is already there. If we try to PUT a file that is already there, the API returns a 422 code, and that is handled by the function in lines 116-126.

If the request fails, it gets logged.

This whole PUT request is done twice, one for the txt report and another one for the html report. Between both, the system waits for 2 seconds. It looks like it is a common issue for the API to fail if too many requests are sent within a short period of time. Therefore, each request is separated from the previous request by at least a couple seconds.

Ideally, the two PUT requests will succeed (and this is what happens most of the time). But, as a last measure of consistency, if only one of them succeeds, the other one will be deleted and the whole resource will need to be re-uploaded. This gives a transaction-like consistency feeling when uploading resources: either all reports are upladed or none. If fail, the upload will be attempted again automatically. There is a maximum amount of retries for this, specified in line 41.

After putting the reports, the git_urls variable (with org, repo, paths, git_urls and SHAs for all reports for all resources) is saved in a local file, for the record.

## Upload of the models

This step only gets executed if we are not in testing mode. Its aim is to store the models in a VertNet administrative repository, to be able to get the values from the previous month directly and re-do the reports if the formatting changes. The function that performs this step is store_models.

The process of uploading the models is the same as the one for uploading the reports. Currently, the models are uploaded to one of my personal repositories, but this will be changed with the final version of the process.

Besides, the URLs of the models are appended to an existing file, the one that is used by find_last_report, in the 'Build the model' section of the generateReports.py module description.

Then, uploadToGithub.py returns the dictionary of git urls, with all the information needed to create amd deliver the issues to notify the users.


# Create issues for each uploaded report

The last part of the process deals with creating issues in the GitHub platform to deliver an email to each user 'watching' the repository, to make them aware of the existence of a new report. All the code related to this part of the process is in the addIssueToGithub.py module.

The module is divided in two sections: generate issues for resources with a report and generate issues for resources without a report.

The code for creating the issues for resources with a report is under the create_issues function. This is just a wrapper to launch the create_issue function for each of the git_url objects.

The create_issue function creates three links for the reports, and puts them in the body of the issue. This three links are: (1) for the report in txt format, (2) for the report in html format, and (3) for the rendered html version of the report. For this last way of rendering the report, we use an external tool that renders HTML files: http://htmlpreview.github.io. The risk we face is that we don't have control over this service, so it can fail or disappear at any time. But the good thing is that the users don't need to download the html file and open it with a browser to see a prettier version of the reports.

Then the function loads the rest of the variables required for POSTing an issue in GitHub using the API. If the POST request fails, it gets logged. If it succeeds, data from the issues are stored in a local file.

The process for delivering notifications of resources with no reports is basically the same, with the difference that there is no link to generate, and the body of the issue is slightly different. But the process is the same, and the response of the API is also stored.

And with that last step, the whole process is finished.


Modes
-----

The process can be launched in several 'modes'. Each mode is valid for certain task, and it has its own launcher. Depending on which launcher is used, the process will perform differently:

* launch.py - The full process.
* launch_to_local - Only for extracting the stats. This launcher will only run the extractStats module, and the resulting pubs dictionary will be stored in a local pickle file. This is useful for testing the generateReports and uploadToGithub modules without having to extract the stats each time.
* launch_from_local - Only generateReports and uploadToGithub, from a local file. It's the inverse of launch_to_local. If we already have a pickle file downloaded, we can avoid having to re-download and generate the stats.
* launch_with_local - A concatenation of launch_to_local and launch_from_local. This should be the standard way of launching the process, since it adds a security layer, downloading the pubs dictionary. If the generateReports or uploadToGithub steps fail, launch_from_local should be executed with the existing local pickle file.
* launch_beta.py - The full process, in beta-testing mode. If this launcher is used, only those beta-testing institutions will receive a report. Beta-testing institutions must appear in the TestingInsts.txt file.
* launch_test - The full process in testing mode. If this launcher is used, only the first ten download events will be scanned, and everything related to GitHub will be done in the testing org and repo (right now, one of my personal repositories).

A note on the from_local mode. You must specify manually the name of the pickle file to be used. My own convention for naming these objects is to use a name like pubs_2014_09_02.pk if the process was run on the 2nd of September, 2014. Launch_to_local and launch_with_local deal with the naming issue (both use this naming convention, and launch_with_local opens the same file after saving it), but launch_from_local requires user input. The name of the file to use must be specified in the launch_from_local file, line 7. It will also assume the process was launched on the day that is specified in the file name, so the log will be creted as if it were launched that day. To override this, comment lines 9-10 and uncomment line 12.


FAQs
----

## You talk about logging stuff. Where can I find the logs?

A new logfile will be generated each time a launcher is executed. It is important to execute the launcher, and not monthlyStatReports, or any individual module, because the launcher configures where and how to log everything. The logs will be found in the logs subfolder, in the project folder, and the name of the files will have this structure: [mode]_[date].log. So for example, if I execute the launch_with_local launcher on the 2nd of September, 2014, the log will be found in logs/with_local_2014_09_02.log

## How do I actually launch the process?

There are three ways of launching the process in a UNIX environment.

1. Simply execute the desired launcher

By executing one of the launchers from command-line, like this:

    $ ./launch_test.py

the corresponding mode will be launched, and the command-line will be blocked until it finishes. Since it is a long process (might last for several hours), I recommend using the second way.

2. Execute the launcher in the background

For that, you just need to modify the command a little bit:

    $ nohup ./launch_test.py &

The nohup will make sure the process doesn't stop if the session is closed, and the final '&' will execute the command in the background, returning the control to the user.

3. Configure a cron task

Especially useful for "production", this allows the process to be run periodically. Currently, a server at CU has a cron task that runs the launch_with_local launcher the 2nd day of each month. The correct way of specifying the task is like this

    0 0 2 * * nohup /path/to/code/folder/launch_with_local.py >> /path/to/cron/log/cron.log 2>&1

This will execute the command nohup /path/to/code/folder/launch_with_local.py and redirect the output of the command (not the logs, jsut if the command failed or not) to the file in /path/to/cron/log/cron.log, making sure errors are also logged in the same file (2>&1), and it will be executed at midnight (0 min, 0 hour) of the 2nd day of each month (first star) of each year (second star).

## How do I check the output?

By reading the corresponding log. I know, the log can be pretty cumbersome and overwhelming, so there is a little trick to know if something went wrong.

In a UNIX environment, execute the following:

    $ cat with_local_2014_09_02.log | grep ERROR

This will only print those lines that have the word 'ERROR'. If nothing is returned, congratulations, there was no error during execution. You can also check the warnings by putting WARNING instead of ERROR.

If you want to check the process while it's running, a similar formula can be used:

    $ cat with_local_2014_09_02.log | tail -n10

This will print the last 10 lines (-n10) of the log file. Useful for checking the current step of the process.

If you launched the process in the background, you can use

    $ jobs

to see the active jobs. But if you closed the session and opened a new one, this won't work. In that case, you need to execute

    $ ps -ef | grep launch_with_local

(changing launch_with_local for the name of the used launcher) to check if it is still running. If nothing appears, the process finished.

In any case, if you launched the process in the background, make sure you check the nohup.out file that is generated after launch, since any problem with the code will be dumped there.

## There was a problem with the naming of GitHub repositories in CartoDB and the report for a resource has not been uploaded. What can I do?

Well, with the latest addition to the code, this shouldn't have happened. But let's assume it did. First of all, check for ERRORs or WARNINGs in the log to see which resource failed (see 'How do I check the output?').

If in fact some report did not make it to the repo, fix the naming issue and re-launch the process, but make sure you specify the launch_from_local launcher to avoid the loong step of downloading the stats (see the note in file naming, at the end of the 'Modes' section). Don't worry about repeated files being uploaded, GitHub throws a special status code for already existing files and the code is ready to detect these cases. If the naming issue was solved, the previously failed resource should be up now.

## I have another question. Can I contact you about it?

Of course! The best way is to send me an email to javier.otegui@gmail.com
