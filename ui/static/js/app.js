var dataObj = {};
var templates = {};
var fileToUpload = '';
var overrideMsg = false;
var editingScreen = false;
var sortField = 'modified_date';
var sortReverse = false;

/**
 * Test if the string is a valid JSON String
 * @param value
 * @returns {boolean}
 * @constructor
 */
function isJson(value) {
    try {
        JSON.parse(value);
    } catch (e) {
        return false;
    }
    return true;
}

/**
 * Upload a data file to the specified data set
 *
 * @param dataSetUrl - the url to the dataset
 * @param uploadFile - The file to upload
 * @param uploadType - (optional) The edit action (create,update). default: create
 * @param onSuccess  - (optional) The success event callback
 */
function uploadData(dataSetUrl, uploadFile, uploadType="create", onSuccess = null){

    var state = "dataset";
    if (uploadType == "create"){
        state = "draft"
    }

    // Check to see if the user is uploading a valid file size
    if (uploadFile.size > templates.uploadMaxSize ){
        alert('[ERROR] The ' + state + ' was '+ uploadType  +'d successfully but the file could not be uploaded ' +
              'You may not upload a file greater than '+ (templates.uploadMaxSize/(1024*1024*1024)) +'GB');
        $('.js-loading').addClass('hide');
        return;
    }

    var csrftoken = getCookie('csrftoken');
    $('.js-loading').removeClass('hide');
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);

        }
    });

    // progress on transfers from the server to the client (downloads)
    function updateProgress (e) {
      if (e.lengthComputable) {
            var pc = parseInt(e.loaded / e.total * 100);
            if (pc >= 100) {
                this.filePointer.progress = pc;
            } else {
                $('.js-progress-wrapper').removeClass('hide');
                $('.js-progress').html(pc);
            }
        }
    }

    function transferError(data) {
       alert('[ERROR] The ' + state + ' was '+ uploadType  +'d successfully but the file could not be uploaded: ' + dataUploadFail(data));
    }

    function transferFailed(data) {
       alert('[FAIL] The  ' + state + ' was '+ uploadType  +'d successfully but the file could not be uploaded: ' + dataUploadFail(data));
    }

    function transferCanceled(data) {
      alert("[ERROR] The transfer has been canceled by the user.");
    }

    function transferSuccess(data) {
        alert('The ' + state + ' has been '+ uploadType  +'d with the attached file.\nPlease note: The page will refresh now and take you back to the list of drafts.');
            $('.js-clear-file').trigger('click');
            $('.js-clear-form').trigger('click');
    }

    function transferComplete(data){
        $('.js-loading').addClass('hide');
    }

    var onError = transferError;
    var onFail = transferFailed;
    var onComplete = transferComplete

    if (!onSuccess) {
        onSuccess = transferSuccess;
    }

    var formData = new FormData();
    formData.append('attachment', uploadFile);
    $('.js-loading').removeClass('hide');
    $.ajax({
        xhr: function () {

            var xhr = new window.XMLHttpRequest();
            xhr.filePointer = formData;
            xhr.upload.filePointer = formData;
            //Upload progress
            xhr.upload.addEventListener("progress", updateProgress, false);

            xhr.addEventListener("progress", updateProgress, false);
            return xhr;
        },
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
        url: dataSetUrl + "upload/",
        success: onSuccess,
        error: onError,
        fail: onFail,
        complete: onComplete,

    });

}

/**
 * Prepare the upload error message from the
 * provided response
 * @param response
 * @returns {string}
 */
function dataUploadFail (response) {
    var errorMessage = response.statusText;
    if (isJson(response.responseText)) {
        errorMessage = response.responseJSON.detail;
    }
    else if (response.readyState == 4){
        // We probably got an HTML page just look for the
        // title of the page
        var el = document.createElement('html');
        el.innerHTML=response.responseText;
        titleElement = el.getElementsByTagName( 'title' )
        // If there is no title use the default error message
        if (titleElement != undefined && titleElement.length > 0 && titleElement[0].innerText) {
            errorMessage = titleElement[0].innerText
        }
    }
    else if (response.readyState == 0)
    {
        errorMessage = "Network Error"
    }

    return errorMessage;
}

function getParameterByName(name, url) {
    if (!url) {
        url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

function isURL(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?' + // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator
    return pattern.test(str);
}

function fileTypeAllowed(filetype) {
    for (var i = 0; i < dataObj.filetypes.length; i++) {
        if (dataObj.filetypes[i].indexOf(filetype) != -1) {
            return dataObj.filetypes[i].indexOf(filetype);
        }
    }

    return -1;
}

function dedupe(array) {
    var returnArray = [];
    $.each(array, function (i, el) {
        if ($.inArray(el, returnArray) === -1) returnArray.push(el);
    });

    return returnArray;
}

$(document).ready(function () {
    $(document).foundation();

    $(window).bind("beforeunload", function (event) {
        if (!overrideMsg) {
            if (window.location.href.indexOf('create') != -1 || (window.location.href.indexOf('edit-list') != -1 && editingScreen)) {
                return confirm("Are you sure you want to leave this page? There may be unsaved changes.");
            }
        }
    });

    if ($('.js-auth').attr('data-auth') == 'false') {
        window.location = 'api/api-auth/login/?next=/';
    } else if ($('.js-auth').attr('data-auth') == 'fluxnet') {
        $('.js-main-article').addClass('hide');
        $('.js-error-article').removeClass('hide');
    }


    csrftoken = getCookie('csrftoken')
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    $.ajax({
        dataType: "json",
        url: '/api/v1/datasets',
        method: 'options',
        success: function (data){
            templates.uploadMaxSize = data['actions']['upload']['parameters']['attachment']['max_length']
        },
        error: function(error){
            console.log(error);
        }
    });

    $.getJSON("static/js/metadata/dataset.json?v=202202", function (data) {
        templates.datasets = data;
        createEditForm('datasets');
    });

    $.getJSON("static/js/metadata/site.json", function (data) {
        templates.sites = data;

    });

    $.getJSON("static/js/metadata/plot.json", function (data) {
        templates.plots = data;

    });

    var viewParam = getParameterByName('view', window.location.href);

    if (viewParam && $('.js-view[data-view="' + viewParam + '"]').length == 1) {
        $('.js-loading').removeClass('hide');
        $('.js-view[data-view="' + viewParam + '"]').removeClass('hide');
        $('.js-home-view').addClass('hide');
    }

    switch (viewParam) {
        case 'create':
            $.when(getDataSets(), getContacts()).then(function (data, contacts) {
                dataObj.datasets = data;
                dataObj.contacts = contacts;
                $('.js-loading').addClass('hide');
            });
            break;

        case 'edit':
            $('.js-loading').addClass('hide');
            break;

        case 'view-sites':
            $('.js-loading').addClass('hide');
            break;

        case 'edit-list':
            $.when(getDataSets(), getContacts()).then(function (data, contacts) {
                dataObj.datasets = data;
                dataObj.contacts = contacts;
                $('.js-text-dump').html('');
                $('.js-datasets').html('');
                dataObj.editDatasets = [];

                // Show datasets managed by the user or if the user is an adminiastrator
                for (var i = 0; i < dataObj.datasets.length; i++) {
                    if ($('.js-auth').attr('data-auth') == 'admin' ||
                        $('.js-auth').attr('data-user') == dataObj.datasets[i].managed_by) {
                        dataObj.editDatasets.push(dataObj.datasets[i]);
                    }
                }
                showEditDatasets();
                $('.js-loading').addClass('hide');
                editingScreen = false;

            });
            break;

        case 'view':
            $.when(getDataSets(), getContacts()).then(function (data, contacts) {
                dataObj.datasets = data;
                dataObj.contacts = contacts;
                $('.js-text-dump').html('');
                $('.js-datasets').html('');
                dataObj.approvedDatasets = [];

                for (var i = 0; i < dataObj.datasets.length; i++) {
                    if (dataObj.datasets[i].status == 2) {
                        dataObj.approvedDatasets.push(dataObj.datasets[i]);
                    }
                }

                showApprovedDatasets();
                $('.js-loading').addClass('hide');
            });
            break;

        default:
            break;
    }


    var popup = new Foundation.Reveal($('#myModal'));
    getFileTypes();

    $.when(getSites()).done(function (sites) {
        dataObj.sites = sites;
        for (var i = 0; i < sites.length; i++) {
            var option = $('<option value="' + sites[i].url + '" data-index="' + i + '">' + sites[i].site_id + ': ' + sites[i].name + '</option>');
            $('.js-all-sites').append(option);
        }
    });

    $.when(getVariables()).done(function (vars) {
        dataObj.variables = vars;
        for (var i = 0; i < vars.length; i++) {
            var option = $('<option value="' + vars[i].url + '" data-index="' + i + '">' + vars[i].name + '</option>');
            $('.js-all-vars').append(option);
        }
    });

    $.when(getPlots()).done(function (plots) {
        dataObj.plots = plots;
        $('.js-all-plots').append('<option value="">None</option>');
        for (var i = 0; i < plots.length; i++) {
            var option = $('<option value="' + plots[i].url + '" data-index="' + i + ' " disabled>' + (plots[i].plot_id ? plots[i].plot_id : 'N/A') + ': ' + plots[i].name + '</option>');
            $('.js-all-plots').append(option);
        }
    });

    populateContacts();

    $('body').on('click', '.js-view-toggle', function (event) {
        var view = $(this).attr('data-view');
        $('.js-view[data-view="' + view + '"]').removeClass('hide');
        window.location = window.location.href + '?view=' + view;
        $('.js-home-view').addClass('hide');
    });

    $('body').on('change', '.js-all-sites', function () {
        var plotTitle = false;
        var index = $(this).find('option:selected').attr('data-index');
        $('.js-view-site-btn .js-site-id').html($(this).val());
        $('.js-site-info').removeClass('hide');

        $('.js-all-plots').removeAttr('disabled');

        var location = {lat: dataObj.sites[index].location_latitude, lng: dataObj.sites[index].location_longitude};
        var map = new google.maps.Map(document.getElementById('js-map-view'), {
            zoom: 4,
            center: location
        });
        var marker = new google.maps.Marker({
            position: location,
            map: map
        });
        $('.js-params').html('');
        $('.js-site-info .js-title').html('').append('<h4>' + dataObj.sites[index]['site_id'] + ': ' + dataObj.sites[index]['name'] + '</h4>');
        for (var prop in dataObj.sites[index]) {
            if (prop != 'site_id' && prop != 'name') {

                if (prop == 'description') {
                    var param = $('<div>' + dataObj.sites[index][prop] + '</div>');
                    $('.js-main-params').html('').append(param);
                } else {
                    var param = $('<div class="row param ' + ((templates.sites[prop] && templates.sites[prop].sequence === -1) ? 'hide' : '') + '"> <div class="columns small-12 medium-3">' + '<b>' + (templates.sites[prop] ? templates.sites[prop].label : prop) + ' </b></div></div>');
                    if (prop == 'contacts') {
                        for (var i = 0; i < dataObj.contacts.length; i++) {
                            if (dataObj.sites[index][prop].indexOf(dataObj.contacts[i].url) != -1) {
                                var contactString = '<div class="columns small-12 medium-9 end float-right">' + dataObj.contacts[i].first_name + ' ' + dataObj.contacts[i].last_name;
                                if (dataObj.contacts[i].email) {
                                    contactString += ' &lt; ' + dataObj.contacts[i].email + ' &gt;';
                                }
                                contactString += '</div>';
                                param.append(contactString);
                            }
                        }
                    } else if (prop == 'pis') {
                        for (var j = 0; j < dataObj.contacts.length; j++) {
                            if (dataObj.sites[index][prop].indexOf(dataObj.contacts[j].url) != -1) {
                                var contactString = '<div class="columns small-12 medium-9 end float-right">' +
                                    dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name;
                                if (dataObj.contacts[j].email) {
                                    contactString += ' &lt; ' + dataObj.contacts[j].email + ' &gt;';
                                }
                                contactString += '</div>';
                                param.append(contactString);
                            }
                        }
                    } else if (prop == 'site_urls') {
                        var urls = dataObj.sites[index][prop].split(',');
                        //param.append('<div class="columns small-12 medium-9 end float-right">');
                        for (var k = 0; k < urls.length; k++) {
                            param.append('<div class="columns small-12 medium-9 end float-right"><a href="' + urls[k] + '">' + urls[k] + '</a></div>');
                        }
                        //param.append('</div>');
                    } else if (prop == 'location_map_url') {
                        param.append('<div class="columns small-12 medium-9 end float-right">' + '<a href="' + dataObj.sites[index][prop] + '">' + (dataObj.sites[index][prop] ? 'Click here' : '') + '</a>' + '</div>');
                    } else {
                        param.append('<div class="columns small-12 medium-9">' + (dataObj.sites[index][prop] ? dataObj.sites[index][prop] : 'N/A') + '</div>');
                    }
                    $('.js-params').append(param);
                }
            }
        }

        var siteStr = '';
        $('.js-all-sites option:selected').each(function () {
            siteStr += $(this).val() + ' ';
        });

        for (var i = 0; i < dataObj.plots.length; i++) {
            if (siteStr.indexOf(dataObj.plots[i].site) != -1) {
                $('.js-all-plots option[value="' + dataObj.plots[i].url + '"]').prop('disabled', false);
                if (!plotTitle) {
                    plotTitle = true;
                    $('.js-params').append('<h4 class="plot-title">Plots in ' + dataObj.sites[index].site_id + '</h4>');
                }
                var plotContainer = $('<div class="plot-info js-plot-info"/>');
                plotContainer.append('<h5>' + dataObj.plots[i].plot_id + ': ' + dataObj.plots[i].name + '</h5>');

                for (var prop in dataObj.plots[i]) {
                    if (prop != 'plot_id' && prop != 'name') {
                        if (prop == 'pi') {
                            for (var j = 0; j < dataObj.contacts.length; j++) {
                                if (dataObj.plots[i][prop] != null) {
                                    if (dataObj.plots[i][prop].indexOf(dataObj.contacts[j].url) != -1) {
                                        var contactString = dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name;
                                        if (dataObj.contacts[j].email) {
                                            contactString += ' &lt; ' + dataObj.contacts[j].email + ' &gt; ';
                                        }

                                        var param = $('<div class="row param ' + (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') + '"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns">' + contactString + '</div></div>');
                                        plotContainer.append(param);
                                    }
                                }
                            }
                        } else if (prop == 'location_kmz_url') {
                            var param = $('<div class="row param ' + (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') + '"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns"><a href="' + dataObj.plots[i][prop] + '">' + (dataObj.plots[i][prop] ? 'Click here' : '') + '</a></div></div>');
                            plotContainer.append(param);
                        } else {
                            var param = $('<div class="row param ' + (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') + '"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns">' + (dataObj.plots[i][prop] ? dataObj.plots[i][prop] : '') + '</div></div>');
                            plotContainer.append(param);
                        }
                    }
                }
                $('.js-params').append(plotContainer);
            } else {
                $('.js-all-plots option[value="' + dataObj.plots[i].url + '"]').each(function () {
                    $(this).prop('disabled', true);
                })
            }

        }

    });

    $('body').on('change', '.js-all-plots', function () {
        var index = $(this).find('option:selected').attr('data-index');
        $('.js-view-plot-btn .js-plot-id').html($(this).val());
        $('.js-plot-info').removeClass('hide');
        $('.js-plot-params').html('');
        for (var prop in dataObj.sites[index]) {
            var param = $('<p>' + prop + ': ' + dataObj.sites[index][prop] + '</p>');
            $('.js-plot-params').append(param);
        }
    });

    function sortByField(a, b) {
        var aName = a[sortField];
        var bName = b[sortField];

        if (aName == null || bName == null) {
            if (sortReverse) {
                return 0;
            } else {
                return 1;
            }
        } else if (aName && bName) {
            aName = a[sortField].toLowerCase();
            bName = b[sortField].toLowerCase();

            if (sortField == 'contact') {
                for (var j = 0; j < dataObj.contacts.length; j++) {
                    if (dataObj.contacts[j].url == a[sortField]) {
                        aName = dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name;
                    }
                    if (dataObj.contacts[j].url == b[sortField]) {
                        bName = dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name;
                    }
                }
            }

            if (sortReverse) {
                return ((aName > bName) ? -1 : ((aName < bName) ? 1 : 0));
            } else {
                return ((aName < bName) ? -1 : ((aName > bName) ? 1 : 0));
            }
        } else {
            if (sortReverse) {
                return 0;
            } else {
                return 1;
            }
        }
    }

    $('body').on('change', '.js-all-contacts', function () {
        if ($(this).val() == 'add-new') {
            $(this).closest('select').removeClass('js-input');
            $(this).closest('select').siblings('.js-new-value').removeClass('hide').addClass('js-input');
        } else {
            $(this).closest('select').addClass('js-input');
            $(this).closest('select').siblings('.js-new-value').addClass('hide').removeClass('js-input');
        }
    });

    $("html").on("dragover", function (event) {
        event.preventDefault();
        event.stopPropagation();
    });

    $("html").on("dragleave", function (event) {
        event.preventDefault();
        event.stopPropagation();
    });

    $("html").on("drop", '.js-file-drop-zone', function (event) {
        event.preventDefault();
        event.stopPropagation();
        var files = event.originalEvent.dataTransfer.files;
        //$('.js-file-input-btn').val(files[0]);
        if (files) {
            if (files.length == 1) {
                $('.js-file-name').html(files[0].name);
                $('.js-file-name-wrapper').removeClass('hide');
                fileToUpload = files[0];
                if ($('.js-existing-file').hasClass('hide')) {
                    $('.js-new-file-msg').removeClass('hide');
                } else {
                    $('.js-file-replace-msg').removeClass('hide');
                }
            } else if (files.length > 1) {
                alert('Only one file is allowed per dataset. If you have multiple files, please compress them into a single file and upload it.');
            }
        }
    });

    $('body').on('click', '.js-clear-file-btn', function (event) {
        event.preventDefault();
        $('.js-file-input-btn').val('');
        $('.js-file-name').html('')
        $('.js-file-name-wrapper').addClass('hide');
        $('.js-new-file-msg').addClass('hide');
        $('.js-file-replace-msg').addClass('hide');
        fileToUpload = false;
    });

    $('body').on('click', '.js-edit-list', function (event) {
        event.preventDefault();
        event.stopPropagation();
        var url = $(this).closest('.js-view-dataset').attr('data-url');
        var index = $(this).closest('.js-view-dataset').attr('data-index');

        if (index != -1) {
            for (var param in templates.datasets) {
                if (param in dataObj.editDatasets[index]) {
                    if (Array.isArray(dataObj.editDatasets[index][param])) {
                        for (var i = 0; i < dataObj.editDatasets[index][param].length; i++) {
                            if (i > 0) {
                                var position = $('.js-edit-form .js-param[data-param="' + param + '"] section').last();
                                var container = position.clone();
                                container.find('.js-input').val(dataObj.editDatasets[index][param][i]);
                                container.insertAfter(position);
                            } else {
                                $('.js-edit-form .js-param[data-param="' + param + '"] .js-input').val(dataObj.datasets[index][param][i]);
                            }
                        }
                    } else {
                        if ($('.js-edit-form .js-param[data-param="' + param + '"] .js-input').hasClass('js-boolean')) {
                            if (dataObj.editDatasets[index][param] == true) {
                                $('.js-edit-form .js-param[data-param="' + param + '"] .js-input.js-true').prop('checked', true);
                            } else if (dataObj.editDatasets[index][param] == false) {
                                $('.js-edit-form .js-param[data-param="' + param + '"] .js-input.js-false').prop('checked', true);
                            }
                        } else {
                            $('.js-edit-form .js-param[data-param="' + param + '"] .js-input').val(dataObj.editDatasets[index][param]);
                        }
                    }
                }
            }
        }
        $('.js-edit-form').attr('data-url', url);
        $('.js-view.view-drafts-view .js-all-datasets').addClass('hide');
        $('.js-edit-form').removeClass('hide');
        $('.js-edit-form .js-edit-dataset').removeClass('hide');
        $('.js-edit-form .js-create-dataset').first().addClass('hide');
        $('.js-edit-form .js-create-dataset.js-submit').addClass('js-submit-dataset').removeClass('js-create-dataset');
        $('.js-edit-form .js-clear-form').addClass('hide');
        $('.js-edit-form .js-cancel-btn').removeClass('hide');
        $('.js-edit-back-btn').removeClass('hide');
        $('.js-edit-form .js-all-plots').removeAttr('disabled');

        if (dataObj.editDatasets[index].status == 0) {
            $('.js-submit-dataset').removeClass('hide');
        } else {
            $('.js-submit-dataset').addClass('hide');
        }

        if (dataObj.editDatasets[index].archive) {
            $('.js-file-exists').removeClass('hide');
            $('.js-existing-file').removeClass('hide')
                .html(dataObj.editDatasets[index].archive_filename);
            $('.js-file-replace-msg').removeClass('hide');
        } else {
            $('.js-file-exists').addClass('hide');
            $('.js-existing-file').addClass('hide');
            $('.js-file-replace-msg').addClass('hide');
        }

        var siteStr = '';
        $('.js-all-sites option:selected').each(function () {
            siteStr += $(this).val() + ' ';
        });

        for (var i = 0; i < dataObj.plots.length; i++) {
            if (siteStr.indexOf(dataObj.plots[i].site) != -1) {
                $('.js-all-plots option[value="' + dataObj.plots[i].url + '"]').each(function () {
                    $(this).prop('disabled', false);
                });
            } else {
                $('.js-all-plots option[value="' + dataObj.plots[i].url + '"]').each(function () {
                    $(this).addClass('disabled', true);
                });
            }
        }
        editingScreen = true;

    });


    $('body').on('click', '.js-file-upload-btn', function (event) {
        event.preventDefault();
        event.stopPropagation();
        $('.js-file-input-btn').trigger('click');
    });

    $(document).on('focus', ".datepicker_recurring_start", function () {
        $(this).datepicker({
            dateFormat: "yy-mm-dd",
            changeMonth: true,
            changeYear: true,
            yearRange: "c-20:c+10"
        });
    });

    $('body').on('change', '.js-file-input-btn', function (event) {
        if (this.files) {
            event.preventDefault();
            event.stopPropagation();
            var dataFile = this.files[0];
            fileToUpload = this.files[0];
            $('.js-file-name').html(this.files[0].name);
            $('.js-file-name-wrapper').removeClass('hide');
            if ($('.js-existing-file').hasClass('hide')) {
                $('.js-new-file-msg').removeClass('hide');
            } else {
                $('.js-file-replace-msg').removeClass('hide');
            }
        }
    });


    $('body').on('click', '.js-delete-dataset', function (event) {
        event.preventDefault();
        var csrftoken = getCookie('csrftoken');
        var url = $(this).attr('data-url');

        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });

        $.ajax({
            method: "DELETE",
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            url: url,
            dataType: "json",
            success: function (data) {
                alert('Dataset deleted');
            },

            fail: function (data) {
                alert('Fail');
            },

            error: function (data, errorThrown) {
                alert('Error: ' + data.statusText);
            },
        });
    });

    $('body').on('click', '.js-cancel-btn', function (event) {
        event.preventDefault();
        overrideMsg = true;
        location.reload();
    })

    $('body').on('click', '.js-save-btn', function (event) {
        event.preventDefault();
        var url = $(this).attr('data-url');
        var id = $(this).attr('data-id');

        var jsonObj = {};

        $('.js-editable-section .js-attr').each(function () {
            var attr = $(this).find('.js-attr-name').html();
            if ($(this).find('.js-attr-val').length > 1) {
                jsonObj[attr] = [];
                $(this).find('.js-attr-val').each(function () {
                    jsonObj[attr].push($(this).val());
                });

            } else if ($(this).find('.js-attr-val').length == 1) {
                jsonObj[attr] = $(this).find('.js-attr-val').val();
            } else if ($(this).find('.js-attr-val').length == 0) {
                jsonObj[attr] = "";
            }

        });
        $.when(submitDataset(jsonObj, url, method="PUT")).done(function (status) {
            if (status.result) {
                var alertMessage = ""
                if (dataObj.editDatasets[i].managed_by == $('.js-auth').attr('data-user')) {
                    $.when(changeStatus(url, "draft")).always(function (response) {
                    if (response.result && response.detail) {
                        alertMessage=response.detail
                    } else {
                        handleFormErrors(submitStatus, "Dataset submission failed. Please check the fields and try again.");
                    }
                    });
                }
                alert(alertMessage + 'Your changes have been saved.\nPlease note: The screen will refresh after you click OK.');
                $('.js-clear-form').trigger('click');
                $('.js-clear-file').trigger('click');

            } else {
                handleFormErrors(status, '\'There was an error with the update.')
            }
        });

    })

    $('body').on('click', '.js-clear-form', function (event) {
        event.preventDefault();
        overrideMsg = true;
        // Always go back to the edit list
        window.location.assign("?view=edit-list")

    });


    $('body').on('click', '.js-submit-dataset', function (event) {
        event.preventDefault();

        var submissionObj = {};
        submissionObj.submit = true;
        var submitMode = true;
        var url = $('.js-edit-form').attr('data-url');

        if (fileToUpload) {

            uploadData(url, fileToUpload, uploadType="update", onSuccess=function (data) {
                    processEditingForm(submissionObj, url);
                });

        } else if (!$('.js-file-exists').hasClass('hide')) {
            processEditingForm(submissionObj, url);
        } else {
            alert('Please upload a file in order to submit the dataset.');
            $('.js-loading').addClass('hide');
        }
    });

    $('body').on('click', '.js-approve', function (event) {
        event.preventDefault();
        event.stopPropagation();
        var approveUrl = $(this).closest('.js-view-dataset').attr('data-url');
        var title = $(this).siblings('.title').text()
        var approve = confirm("Approve Dataset: " + title);
        if (approve) {

            $.when(changeStatus(approveUrl, "approve")).always(function (xhrResponse) {
                if (xhrResponse.result == true){
                    alert("Dataset Approved")

                    // refreshes the page
                    history.go(0);
                }
                else {
                    alert(xhrResponse.responseJSON.detail)
                }


            });
        }

    });

    $('body').on('click', '.js-review', function (event) {
        event.preventDefault();
        event.stopPropagation();
        var approveUrl = $(this).closest('.js-view-dataset').attr('data-url');
        var title = $(this).siblings('.title').text()
        var approve = confirm("Request Review of Dataset: " + title);
        if (approve) {

            $.when(changeStatus(approveUrl, "submit")).always(function (xhrResponse) {
                if (xhrResponse.result == true){
                    alert("Dataset Review Requested")

                    // refreshes the page
                    history.go(0);
                }
                else {
                    alert(xhrResponse.responseJSON.detail)
                }
            });
        }

    });

    $('body').on('click', '.js-create-dataset', function (event) {
        event.preventDefault();
        var submissionObj = {};
        submissionObj.submit = true;
        var submitMode = false;

        if ($(this).hasClass('js-submit')) {
            submitMode = true;
        }

        $('.js-param.missing').each(function () {
            $(this).removeClass('missing');
        });

        var entryCount = 0;
        var validEntries = true;

        //find all the contacts and authors first before processing others
        if ($('.js-new-value.js-input').length > 0) {

            $('.js-new-value.js-input').each(function (index) {
                if (!$(this).find('.js-first-name').val() || !$(this).find('.js-last-name').val() || !$(this).find('.js-email').val()) {
                    validEntries = false;
                }
            });

            if (validEntries) {

                $('.js-new-value.js-input').each(function (index) {

                    var param = $(this).closest('.js-param').attr('data-param');
                    var fname = $(this).find('.js-first-name').val();
                    var lname = $(this).find('.js-last-name').val();
                    var email = $(this).find('.js-email').val();
                    var orcid = $(this).find('.js-orcid').val();

                    $.when(createContact(fname, lname, email, '', orcid)).done(function(status) {
                        if (status.url && entryCount == $('.js-new-value.js-input').length - 1) {
                            if (!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            } else if (param == 'contact') {
                                submissionObj[param] = status.url;
                            } else if (param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                            submissionObj = processForm(submissionObj, submitMode);
                            // no properties are specified. note that ngee tropics resources will always be set
                            // submit will also be present, which will be removed in the createDraft method
                            createDraft(submissionObj, submitMode);

                        } else if (status.url) {
                            if (!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            } else if (param == 'contact') {
                                submissionObj[param] = status.url;
                            } else if (param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                        } else {
                            var responseStr = '';
                            if (status.responseText) {

                                var response = JSON.parse(status.responseText);
                                for (var prop in response) {
                                    responseStr += prop + ': ' + response[prop] + '\n';
                                }
                            }
                            alert('There was a problem creating the new collaborator.\n' + responseStr);
                            return;
                        }
                    });

                });
            } else {
                alert('Please enter first and last names, and email address for all new contacts/authors');
            }
        } else {
            $('.js-loading').removeClass('hide');
            submissionObj = processForm(submissionObj, submitMode);
            createDraft(submissionObj, submitMode);

        }

    });

    $('body').on('click', '.js-edit-dataset', function (event) {
        event.preventDefault();
        var url = $('.js-edit-form').attr('data-url');
        var submissionObj = {};
        var validEntries = true;
        var entryCount = 0;
        if ($('.js-new-value.js-input').length > 0) {

            $('.js-new-value.js-input').each(function (index) {
                if (!$(this).find('.js-first-name').val() || !$(this).find('.js-last-name').val()) {
                    validEntries = false;
                }
            });

            if (validEntries) {
                $('.js-loading').removeClass('hide');
                $('.js-new-value.js-input').each(function (index) {

                    var param = $(this).closest('.js-param').attr('data-param');

                    var fname = $(this).find('.js-first-name').val();
                    var lname = $(this).find('.js-last-name').val();
                    var email = $(this).find('.js-email').val();
                    var orcid = $(this).find('.js-orcid').val();

                    $.when(createContact(fname, lname, '', '', orcid)).done(function(status) {
                        if (status.url && entryCount == $('.js-new-value.js-input').length - 1) {
                            if (!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            } else if (param == 'contact') {
                                submissionObj[param] = status.url;
                            } else if (param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                            submissionObj = processForm(submissionObj, false, true);

                            // no properties are specified. note that ngee tropics resources will always be set
                            // submit will also be present, which will be removed in the createDraft method
                            completeEdit(submissionObj, url);

                        } else if (status.url) {
                            if (!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            } else if (param == 'contact') {
                                submissionObj[param] = status.url;
                            } else if (param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                        } else {
                            var responseStr = '';
                            if (status.responseText) {

                                var response = JSON.parse(status.responseText);
                                for (var prop in response) {
                                    responseStr += prop + ': ' + response[prop] + '\n';
                                }
                            }
                            alert('There was a problem creating the new entry.\n' + responseStr);
                            $('.js-loading').addClass('hide');

                            return;
                        }
                    });

                });
            } else {
                alert('Please enter first and last names, and email for all new contacts/authors');
            }

        } else {
            $('.js-loading').removeClass('hide');
            submissionObj = processForm(submissionObj, false, true);
            completeEdit(submissionObj, url);
        }
    });

    $('body').on('click', '.js-create-contact', function (event) {
        event.preventDefault();
        var parent = $(this).closest('.js-new-value');
        var fname = parent.find('.js-first-name').val().trim();
        var lname = parent.find('.js-last-name').val().trim();
        var email = parent.find('.js-email').val().trim();
        var orcid = parent.find('.js-orcid').val().trim();

        if (fname && lname && email) {

        $.when(createContact(fname, lname, email, '', orcid)).done(function(status) {
            if(status.url) {

                alert('Collaborator has been added.');
                $('.js-all-contacts').each(function() {
                    $(this).append('<option value="'+ status.url +'">' + lname + ', ' + fname + '</option>');
                });
                parent.closest('.js-contact-section').find('select').val(status.url)
                                                    .addClass('js-input');
                parent.addClass('hide').removeClass('js-input');


            }
            else {
                var errorMsg = 'The following error(s) have occurred:\n\n';
                for(var obj in status.responseJSON) {
                    errorMsg += status.responseJSON[obj] + '\n';
                }
                alert(errorMsg)
            }});

        } else {
            alert('Please enter fist and last name, and email.');
        }

    });

    $('body').on('click', '.js-get-datasets', function (event) {
        event.preventDefault();

    });

    $('body').on('click', '.js-del-param', function (event) {
        $(this).closest('section').remove();
    });

    $('body').on('click', '.js-sort-header', function () {
        var newSortField = $(this).attr('data-sort');
        if (newSortField == sortField) {
            sortReverse = !sortReverse;
        } else {
            sortField = newSortField;
        }

        $('.js-sort-icon.unsorted').removeClass('hide');
        $('.js-sort-icon.sort-up').addClass('hide');
        $('.js-sort-icon.sort-down').addClass('hide');

        if (sortReverse) {
            $(this).find('.sort-down').removeClass('hide');
            $(this).find('.sort-up').addClass('hide');
            $(this).find('.unsorted').addClass('hide');
        } else {
            $(this).find('.sort-up').removeClass('hide');
            $(this).find('.sort-down').addClass('hide');
            $(this).find('.unsorted').addClass('hide');
        }
        if (dataObj.approvedDatasets) {
            dataObj.approvedDatasets.sort(sortByField);
            showApprovedDatasets();
        }
        if (dataObj.editDatasets) {
            dataObj.editDatasets.sort(sortByField);
            showEditDatasets();
        }

    });

    $('body').on('click', '.js-view-dataset', function (event) {
        event.preventDefault();
        var index = $(this).attr('data-index');
        var url = $(this).attr('data-url');

        $.when(getDataSets(url)).done(function (datasetObj) {
            $('#myModal #modalTitle').html('')
                .html('<div class="row js-title-row"><div class="columns small-12 medium-9">' + datasetObj['name'] + '</div><div class="columns small-12 medium-3 js-download-wrapper download-wrapper"></div></div>');
            $('#myModal .js-modal-body').html('');
            var inputString = '';
            var citation = '';

            for (var prop in templates.datasets) {
                if (prop in datasetObj && templates.datasets[prop].sequence != -1 && datasetObj[prop] != null && datasetObj[prop].length > 0) {

                    var substring = '<div class="row">';

                    substring += '<div class="columns small-12 medium-3"><b class="js-param-name ' + prop + '">' + templates.datasets[prop].label + (templates.datasets[prop].multiple ? '(s)' : '') + '</b>' + '&nbsp;</div>';
                    if ((prop == 'contact' || prop == 'sites' || prop == 'plots' || prop == 'authors' || prop == 'variables' || prop == 'cdiac_submission_contact') && datasetObj[prop] && datasetObj[prop] != null) {
                        if (prop == 'contact' || prop == 'authors' || prop == 'cdiac_submission_contact') {
                            if (Array.isArray(datasetObj[prop])) {
                                for (var q = 0; q < datasetObj[prop].length; q++) {
                                    for (var i = 0; i < dataObj.contacts.length; i++) {
                                        if (datasetObj[prop][q].indexOf(dataObj.contacts[i].url) != -1) {
                                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val ' + prop + '">' +
                                                dataObj.contacts[i].first_name + ' ' +
                                                dataObj.contacts[i].last_name;
                                            if (dataObj.contacts[i].email) {
                                                substring += ' &lt; ' + dataObj.contacts[i].email + ' &gt;';
                                            }
                                            substring += '</span></div>';
                                        }

                                        if (prop == 'authors' && datasetObj[prop][q].indexOf(dataObj.contacts[i].url) != -1) {
                                            citation += dataObj.contacts[i].first_name + ' ' + dataObj.contacts[i].last_name + ', ';
                                        }
                                    }
                                }
                            } else {
                                for (var i = 0; i < dataObj.contacts.length; i++) {
                                    if (datasetObj[prop].indexOf(dataObj.contacts[i].url) != -1) {
                                        substring += '<div class="columns small-12 medium-9"><span class="js-param-val ' + prop + '">' +
                                            dataObj.contacts[i].first_name + ' ' +
                                            dataObj.contacts[i].last_name;
                                        if (dataObj.contacts[i].email) {
                                            substring += ' &lt; ' + dataObj.contacts[i].email + ' &gt;';
                                        }
                                        substring += '</span></div>';
                                    }
                                }
                            }
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));

                        } else if (prop == 'sites') {
                            for (var j = 0; j < dataObj.sites.length; j++) {
                                if (datasetObj[prop].indexOf(dataObj.sites[j].url) != -1) {
                                    substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.sites[j].site_id + ': ' + dataObj.sites[j].name + '</span></div>';

                                }
                            }
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        } else if (prop == 'plots') {
                            for (var l = 0; l < dataObj.plots.length; l++) {
                                if (datasetObj[prop].indexOf(dataObj.plots[l].url) != -1) {
                                    substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.plots[l].plot_id + ': ' + dataObj.plots[l].name + '</span></div>';

                                }
                            }
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        } else if (prop == 'variables') {
                            for (var m = 0; m < dataObj.variables.length; m++) {
                                if (datasetObj[prop].indexOf(dataObj.variables[m].url) != -1) {
                                    substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.variables[m].name + '</span></div>';

                                }
                            }
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        }
                    } else if (prop == 'access_level') {
                        for (var k = 0; k < templates.datasets.access_level.choices.length; k++) {
                            if (datasetObj[prop] == templates.datasets.access_level.choices[k].value) {
                                substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + templates.datasets.access_level.choices[k].display_name + '</span></div>';
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }
                        }
                    } else if (prop == 'ngee_tropics_resources') {
                        if (datasetObj[prop] == true) {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + 'Yes' + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        } else if (datasetObj[prop] == false) {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + 'No' + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        } else {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        }
                    } else if (prop == 'qaqc_status') {
                        for (var n = 0; n < templates.datasets.qaqc_status.choices.length; n++) {
                            if (datasetObj[prop] == templates.datasets.qaqc_status.choices[n].value) {
                                substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + templates.datasets.qaqc_status.choices[n].display_name + '</span></div>';
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }
                        }
                    } else if (prop == 'doi') {
                        substring += '<div class="columns small-12 medium-9"><a href="' + (datasetObj[prop] == null ? '' : datasetObj[prop]) + '"><span class="js-param-val">' + (datasetObj[prop] == null ? '' : datasetObj[prop]) + '</span></a></div>';
                        $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                    } else {
                        if (prop == 'cdiac_submission_contact') {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + ($('.js-param-val.contact').html() ? $('.js-param-val.contact').html() : 'N/A') + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        } else {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + (datasetObj[prop] == null ? 'N/A' : datasetObj[prop]) + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        }
                    }


                }

            }
            if (citation.length >= 2) {
                citation = citation.substring(0, citation.length - 2);

            }
            if (datasetObj['submission_date'])
                citation += '(' + datasetObj['submission_date'].substring(0, 4) + '). ';

            citation += datasetObj['name'] + '. ' + 'NGEE Tropics Data Collection. Accessed at <a href="' + datasetObj['doi'] + '">' + datasetObj['doi'] + '</a>.';
            if (!datasetObj['doi']) {
                citation = 'Citation information not available currently. Contact dataset author(s) for citation or acknowledgement text.';
            }
            $('#myModal .js-modal-body').append('<div class="row js-dataset-row dataset-row"><div class="columns small-12 medium-3"><b class="js-param-name">Dataset Citation</b></div>'
                + '<div class="columns small-12 medium-9">' + citation + '</div></div>');

            $('#myModal .js-save-btn').attr('data-url', datasetObj['url'])
                .attr('data-id', datasetObj['data_set_id']);

            if (dataObj.datasets[index]['archive']) {
                $('.js-file-download-btn').attr('data-url', datasetObj['url'])
                    .attr('data-archive', datasetObj['archive'])
                    .attr('href', datasetObj['archive'])
                    .addClass('pull-right');
                $('.js-download-wrapper').removeClass('hide');
            }

            //}
            if (!datasetObj.archive) {
                $('.js-data-policy-text').addClass('hide');
                $('.js-file-download-btn').addClass('hide');
            } else {
                $('.js-data-policy-text').removeClass('hide');
                $('.js-file-download-btn').removeClass('hide');
            }
            $('.js-data-policy-check').prop('checked', false);
            $('.js-file-download-btn').addClass('disabled');
            popup.open();
        });

    });

    $('body').on('click', '.js-data-policy-check', function () {
        if ($('.js-data-policy-check').prop('checked')) {
            $('.js-file-download-btn').removeClass('disabled');
        } else {
            $('.js-file-download-btn').addClass('disabled');
        }
    });

    $('body').on('click', '.js-close-modal', function (event) {
        event.preventDefault();
        popup.close();
    });

    $('body').on('click', '.js-get-sites', function (event) {
        event.preventDefault();
        $.when(getSites()).then(function (data) {
            dataObj.sites = data;
            $('.js-text-dump').html('');
            for (var i = 0; i < data.length; i++) {
                $('.js-text-dump').append('Site Name: ' + (data[i].name ? data[i].name : 'NA') + '<br>')
                    .append('ID: ' + (data[i].siteId ? data[i].siteId : 'NA') + '<br>')
                    .append('Description: ' + (data[i].description ? data[i].description : 'NA') + '<br>')
                    .append('Country: ' + (data[i].country ? data[i].country : 'NA') + '<br>')
                    .append('State/Province: ' + (data[i].stateProvince ? data[i].stateProvince : 'NA') + '<br>')
                    .append('UTC Offset: ' + (data[i].utcOffset ? data[i].utcOffset : 'NA') + '<br>')
                    .append('Latitude: ' + (data[i].locationLatitude ? data[i].locationLatitude : 'NA') + '<br>')
                    .append('Longitude: ' + (data[i].locationLongitude ? data[i].locationLongitude : 'NA') + '<br>')
                    .append('Elevation: ' + (data[i].locationElevation ? data[i].locationElevation : 'NA') + '<br>')
                    .append('Location URL: ' + (data[i].locationMapUrl ? data[i].locationMapUrl : 'NA') + '<br>')
                    .append('Bounding Box Ul Lat: ' + (data[i].locationBoundingBoxUlLatitude ? data[i].locationBoundingBoxUlLatitude : 'NA') + '<br>')
                    .append('Bounding Box Ul Lon: ' + (data[i].locationBoundingBoxUlLongitude ? data[i].locationBoundingBoxUlLongitude : 'NA') + '<br>')
                    .append('Bounding Box Lr Lat: ' + (data[i].locationBoundingBoxLrLatitude ? data[i].locationBoundingBoxLrLatitude : 'NA') + '<br>')
                    .append('Bounding Box Lr Lat: ' + (data[i].locationBoundingBoxLrLongitude ? data[i].locationBoundingBoxLrLongitude : 'NA') + '<br>')
                    .append('Site URL: ' + (data[i].siteUrls ? data[i].siteUrls : 'NA') + '<br>')
                    .append('Submission Date: ' + (data[i].submissionDate ? data[i].submissionDate : 'NA') + '<br>')
                    .append('Submission: ' + (data[i].submission ? data[i].submission : 'NA') + '<br><br>');
            }
        });
    });

    $('body').on('click', '.js-get-plots', function (event) {
        event.preventDefault();
        $.when(getPlots()).then(function (data) {
            dataObj.plots = data;
            $('.js-text-dump').html('');
            for (var i = 0; i < data.length; i++) {
                $('.js-text-dump').append('Plot ID: ' + (data[i].plotId ? data[i].plotId : 'NA') + '<br>')
                    .append('Name: ' + (data[i].name ? data[i].name : 'NA') + '<br>')
                    .append('Description: ' + (data[i].description ? data[i].description : 'NA') + '<br>')
                    .append('Size: ' + (data[i].size ? data[i].size : 'NA') + '<br>')
                    .append('Elevation: ' + (data[i].locationElevation ? data[i].locationElevation : 'NA') + '<br>')
                    .append('KMZ URL: ' + (data[i].locationKmzUrl ? data[i].locationKmzUrl : 'NA') + '<br>')
                    .append('Submission Date: ' + (data[i].submissionDate ? data[i].submissionDate : 'NA') + '<br>')
                    .append('PI: ' + (data[i].pi ? data[i].pi : 'NA') + '<br>')
                    .append('Site: ' + (data[i].site ? data[i].site : 'NA') + '<br>')
                    .append('Submission: ' + (data[i].submission ? data[i].submission : 'NA') + '<br><br>');

            }
        });
    });

    $('body').on('click', '.js-add-new', function (event) {
        event.preventDefault();
        var input = $(this).closest('.js-param').find('.js-multi-container').first().clone();
        $(input).val('')
            .prop('checked');
        if (input.attr('data-list') == 'contacts') {
            input.find('.js-new-value').addClass('hide').removeClass('js-input');
            input.find('.js-first-name').val('');
            input.find('.js-last-name').val('');
            input.find('.js-email').val('');
            input.find('.js-orcid').val('');
        }
        input.insertBefore(this);
    });

});

function createDraft(submissionObj, submitMode) {
    if (submissionObj.submit) {
        if (submitMode && !fileToUpload) {
            alert('Please upload an archive file in order to submit the dataset.');
            $('.js-loading').addClass('hide');
        } else {
            $('.js-loading').removeClass('hide');
            delete submissionObj.submit;
            $.when(submitDataset(submissionObj)).done(function (statusObj) {
                if (statusObj.result || statusObj.status == '0') {
                    if (fileToUpload) {

                       uploadData(statusObj.url, fileToUpload, uploadType="create",onSuccess = function (data) {
                                if (submitMode) {
                                    $.when(changeStatus(statusObj.url, "submit")).always(function (submitStatus) {
                                        if (submitStatus.result) {
                                            alert(submitStatus.detail + '\n\nPlease note: The screen will refresh after you click OK.');
                                            $('.js-clear-form').trigger('click');
                                            $('.js-clear-file').trigger('click');
                                        } else {
                                            handleFormErrors(submitStatus, "Dataset submission failed. Please check the fields and try again.");
                                        }
                                    });
                                } else {
                                    alert('Dataset has been created with the attached file.\nPlease note: The screen will refresh after you click OK.');
                                    $('.js-clear-form').trigger('click');
                                    $('.js-clear-file').trigger('click');
                                }
                            });

                    } else {
                        alert('Dataset has been created successfully. You can make further changes to it by going to Home > Edit Drafts.\nPlease note: The screen will refresh after you click OK.');
                        $('.js-clear-form').trigger('click');
                        $('.js-clear-file').trigger('click');
                        $('.js-loading').addClass('hide');
                    }
                } else {
                    handleFormErrors(statusObj, "There was an error creating the draft.");
                    $('.js-loading').addClass('hide');
                }

            });
        }

    } else {
        alert('Please fill all the required fields.');
        $('.js-loading').addClass('hide');
        $('body').animate({
            scrollTop: $('.js-create-form').offset().top
        }, 500);
    }
}

function showEditDatasets() {
    var approvedCount = 0;
    $('.js-all-datasets table tbody').html('');
    for (var i = 0; i < dataObj.editDatasets.length; i++) {

        var tr = $('<tr/>');
        tr.append('<td>' + dataObj.editDatasets[i].data_set_id + '</td>');
        var tag = $('<td/><div/>').addClass('js-view-dataset dataset');
        tag.append('<h5 class="title">' + (dataObj.editDatasets[i].name ? dataObj.editDatasets[i].name : 'NA') + '</h5>')
            .append('<p class="desc">' + (dataObj.editDatasets[i].description ? dataObj.editDatasets[i].description.substring(0, 199) + '...' : 'NA') + '</p>')
            .attr('data-url', dataObj.editDatasets[i].url)
            .attr('data-index', i)
            .attr('data-url', dataObj.editDatasets[i].url)
            .attr('data-index', i);

            tag.append('<button class="button js-edit-list">Edit</button>');
            if ($('.js-auth').attr('data-auth') == 'admin' && dataObj.editDatasets[i].needs_approval)
            {
                tag.append(' <button class="button blue js-approve">Approve</button>');
            }
            if ($('.js-auth').attr('data-user') == dataObj.editDatasets[i].managed_by && dataObj.editDatasets[i].needs_review)
            {
                tag.append(' <button class="button blue js-review">Request Review</button>');
            }

        tr.append(tag);

        var contact = false;
        for (var j = 0; j < dataObj.contacts.length; j++) {
            if (dataObj.contacts[j].url.indexOf(dataObj.editDatasets[i].contact) != -1) {
                contact = true;
                tr.append('<td>' + dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name + '</td>');
            }
        }

        if (!contact) {
            tr.append('<td></td>');
        }

        if (dataObj.editDatasets[i].publication_date) {
            tr.append('<td>' + new Date(dataObj.editDatasets[i].publication_date).toLocaleString() + '</td>');
        }
        else {
            tr.append('<td></td>');
        }

        switch (dataObj.editDatasets[i].status) {
            case "0":
                tr.append('<td>Draft</td>');
                break;

            case "1":
                tr.append('<td>Submitted</td>');
                break;
            case "2":
                tr.append('<td>Approved</td>');
                break;
            default:
                tr.append('<td></td>');
                break;
        }
        ;

        tr.append('<td>' + new Date(dataObj.editDatasets[i].modified_date).toLocaleString() + '</td>');

        approvedCount++;

        switch (dataObj.editDatasets[i].access_level) {
            case '0':
                tr.append('<td>Private</td>');
                break;

            case '1':
                tr.append('<td>NGEE Tropics</td>');
                break;

            case '2':
                tr.append('<td>Public</td>');
                break;
            default:
                tr.append('<td></td>');
                break;
        }

        $('.js-all-datasets tbody').append(tr);


    }
    $('.js-view.view-drafts-view h4 .js-count').html(approvedCount);
}

function showApprovedDatasets() {
    var approvedCount = 0;
    $('.js-all-datasets table tbody').html('');
    for (var i = 0; i < dataObj.approvedDatasets.length; i++) {

        if (dataObj.approvedDatasets[i].status == 2) {
            var tr = $('<tr/>');
            tr.append('<td>' + dataObj.approvedDatasets[i].data_set_id + '</td>');
            var tag = $('<td/><div/>').addClass('js-view-dataset dataset');
            tag.append('<h5 class="title">' + (dataObj.approvedDatasets[i].name ? dataObj.approvedDatasets[i].name : 'NA') + '</h5>')
                .append('<p class="desc">' + (dataObj.approvedDatasets[i].description ? dataObj.approvedDatasets[i].description.substring(0, 199) + '...' : 'NA') + '</p>')
                .attr('data-url', dataObj.approvedDatasets[i].url)
                .attr('data-index', i);

            tr.append(tag);

            for (var j = 0; j < dataObj.contacts.length; j++) {
                if (dataObj.contacts[j].url.indexOf(dataObj.approvedDatasets[i].contact) != -1) {
                    tr.append('<td>' + dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name + '</td>');
                }
            }

            if (dataObj.approvedDatasets[i].publication_date) {
                tr.append('<td>' + new Date(dataObj.approvedDatasets[i].publication_date).toLocaleString() + '</td>');
            }


            switch (dataObj.approvedDatasets[i].status) {
                case "0":
                    tr.append('<td>Draft</td>');
                    break;

                case "1":
                    tr.append('<td>Submitted</td>');
                    break;

                case "2":
                    tr.append('<td>Approved</td>');
                    break;

                default:
                    tr.append('<td></td>');
                    break;
            }
            ;

            tr.append('<td>' + new Date(dataObj.approvedDatasets[i].modified_date).toLocaleString() + '</td>');

            approvedCount++;

            switch (dataObj.approvedDatasets[i].access_level) {
                case '0':
                    tr.append('<td>Private</td>');
                    break;

                case '1':
                    tr.append('<td>NGEE Tropics</td>');
                    break;

                case '2':
                    tr.append('<td>Public</td>');
                    break;
            }

            $('.js-all-datasets tbody').append(tr);

        }

    }
    $('.js-view.view-dataset-view h4 .js-count').html(approvedCount);
}

function completeEdit(submissionObj, url, submitMode) {
    if (!submissionObj['plots']) {
        submissionObj['plots'] = [];
    }

    if (!submissionObj['sites']) {
        submissionObj['sites'] = [];
    }

    $.when(submitDataset(submissionObj, url, method="PUT")).done(function (data) {
        if (data.result) {

            if (fileToUpload) {

                uploadData(url, fileToUpload, uploadType='update');

            } else {
                var alertMessage = ""
                if (data.managed_by == $('.js-auth').attr('data-user')) {
                    $.when(changeStatus(url, "draft")).always(function (response) {
                    if (response.result && response.detail) {
                        alertMessage=response.detail
                    } else {
                        handleFormErrors(submitStatus, "Dataset submission failed. Please check the fields and try again.");
                    }
                    });
                }
                alert(alertMessage + 'Dataset has been updated successfully.\nPlease note: The screen will refresh after you click OK.');
                $('.js-clear-form').trigger('click');
                $('.js-clear-file').trigger('click');

            }
        } else {
            handleFormErrors(data, "There was an error with the update.");
            $('.js-loading').addClass('hide');
        }
    });

}

function processForm(submissionObj, submitMode, editMode) {
    var params = $('.js-create-form .js-param');

    if (editMode) {
        params = $('.js-edit-form .js-param');
    }

    params.each(function () {
        var param = $(this).attr('data-param');
        var required = $(this).hasClass('required');
        var multi = $(this).hasClass('multi')

        $(this).find('.js-input').each(function () {
            if ($(this).val() != null) {
                if ($(this).val().trim()) {
                    if ($(this).hasClass('js-new-value')) {
                        ;
                    } else if ($(this).hasClass('js-boolean')) {
                        if ($(this).prop('checked') && $(this).val() == 'true') {
                            submissionObj[param] = true;
                        } else if ($(this).prop('checked') && $(this).val() == 'false') {
                            submissionObj[param] = false;
                        }

                        if ($('.js-boolean:checked').length == 0 && submitMode) {
                            submissionObj.submit = false;
                            $(this).closest('.js-param').addClass('missing');
                        }
                    } else if (multi) {
                        if (!submissionObj[param]) {
                            submissionObj[param] = [];
                        }
                        submissionObj[param].push($(this).val().trim());
                    } else {
                        submissionObj[param] = $(this).val().trim();
                    }
                } else if (editMode && !$(this).val().trim()) {

                    if (multi) {
                        if (!submissionObj[param]) {
                            submissionObj[param] = [];
                        }
                    } else {
                        submissionObj[param] = null;
                    }

                } else if (submitMode && required) {
                    if ($(this).hasClass('js-new-value') && submissionObj[param]) {
                        ;
                    } else {
                        submissionObj.submit = false;
                        $(this).closest('.js-param').addClass('missing');
                    }
                }

            } else if ($(this).val() == null && submitMode && required) {
                submissionObj.submit = false;
                $(this).closest('.js-param').addClass('missing');
            }

        });
    });

    for (var prop in submissionObj) {
        if (Array.isArray(submissionObj[prop])) {
            submissionObj[prop] = dedupe(submissionObj[prop]);
        }
    }

    return submissionObj;
}

function populateContacts() {
    var deferObj = jQuery.Deferred();
    $.when(getContacts()).done(function (contacts) {
        dataObj.contacts = contacts;
        $('.js-all-contacts').append('<option value="add-new" data-index="-1" class="add-new-option"> - Add Collaborator - </option>');
        for(var i=0;i<contacts.length;i++) {
            var contactDisplay =  contacts[i].last_name + ', ' + contacts[i].first_name
            if (contacts[i].orcid.length > 0) {
                contactDisplay += " (" +contacts[i].orcid + ")";
            }
            var option = $('<option value="'+ contacts[i].url +'" data-index="' + i + '">' + contactDisplay + '</option>');
            $('.js-all-contacts').append(option);
        }
        return deferObj.resolve(true);

    });

    return deferObj.promise();
}

function createEditForm(templateType) {
    var formHTML = $('<div/>');
    var paramHTML = '';
    for (var param in templates[templateType]) {
        if (templates[templateType][param].read_only) {
            paramHTML = $('<input type="hidden">').addClass(param + (templates[templateType][param].required ? "required" : "") + ' js-param')
                .val(templates[templateType][param].value)
                .attr('data-param', param);
        } else {
            paramHTML = $('<div class="js-param ' + (templates[templateType][param].required ? ' required ' : '') + (templates[templateType][param].multiple ? ' multi ' : '') + ' param"></div>').addClass(param)
                .attr('data-param', param);
            var label = templates[templateType][param].label;

            if (templates[templateType][param].multiple) {
                label += '(s)';
            }

            if (templates[templateType][param].required) {
                label += '<i class="required">*</i>';
            }

            var tooltip = '<b class="desc-tooltip js-tooltip" title="' + templates[templateType][param].description + '" > ?</b>';

            paramHTML.append($('<span class="js-display-name display-name"></span>').html(label + '&nbsp;&nbsp;' + tooltip));
            switch (templates[templateType][param].type) {
                case "string":
                    var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();
                    if (templates[templateType][param].max_length) {
                        tag.attr('maxlength', templates[templateType][param].max_length);
                    }
                    tag.removeClass('js-template').addClass('js-input');
                    paramHTML.append(tag);
                    break;

                case "date":
                    var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();
                    tag.removeClass('js-template').addClass('js-input');
                    paramHTML.append(tag);
                    break;

                case "datetime":
                    var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();
                    tag.removeClass('js-template').addClass('js-input');
                    paramHTML.append(tag);
                    break;

                case "boolean":
                    var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();
                    var d = new Date();
                    var n = d.getTime();
                    tag.find('.js-true').attr('id', 'true-' + n);
                    tag.find('.js-true-label').attr('for', 'true-' + n);
                    tag.find('.js-false').attr('id', 'false-' + n);
                    tag.find('.js-false-label').attr('for', 'false-' + n);
                    tag.removeClass('js-template');
                    paramHTML.append(tag);
                    break;

                case "choice":
                    var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();

                    for (var choice in templates[templateType][param].choices) {
                        var option = $('<option/>').val(templates[templateType][param].choices[choice].value)
                            .html(templates[templateType][param].choices[choice].display_name);
                        tag.append(option);
                    }
                    tag.removeClass('js-template').addClass('js-input');
                    paramHTML.append(tag);
                    break;

                case "reference_list":
                    var list = templates[templateType][param]['list_name'];
                    $('.js-ref-list[data-list="' + list + '"]').clone().removeClass('hide').appendTo(paramHTML);
                    break;

                default:
                    var tag = $('<textarea/>').addClass('js-input');
                    paramHTML.append(tag);
                    break;
            }

            if (templates[templateType][param].multiple) {
                var multiBtn = $('.js-add-new').clone();
                var delBtn = $('.js-del-param').clone();
                multiBtn.attr('data-param', param);
                delBtn.attr('data-param', param);
                paramHTML.append(multiBtn);
                delBtn.insertAfter(paramHTML.find('.js-input'));
            }

        }

        $(formHTML).append(paramHTML);
    }
    $('.js-create-form').prepend(formHTML);

    var editForm = $('.js-create-form').clone();
    editForm.removeClass('js-create-form').addClass('js-edit-form hide').appendTo('.js-view.view-drafts-view');
    var d = new Date();
    var n = d.getTime();
    editForm.find('.js-true').attr('id', 'true-' + n);
    editForm.find('.js-true-label').attr('for', 'true-' + n);
    editForm.find('.js-false').attr('id', 'false-' + n);
    editForm.find('.js-false-label').attr('for', 'false-' + n);

    $('.js-input.date').datepicker({
        dateFormat: "yy-mm-dd",
        changeMonth: true,
        changeYear: true,
        yearRange: "c-20:c+10"
    });

    $('.js-tooltip').popover({trigger: "manual", html: true, animation: false, placement: 'right'})
        .on("mouseenter", function () {
            var _this = this;
            $(this).popover("show");
            $(".popover").on("mouseleave", function () {
                $(_this).popover('hide');
            });
        }).on("mouseleave", function () {
        var _this = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("hide");
            }
        }, 300);
    });
    $('.js-file-tooltip').popover({trigger: "manual", html: true, animation: false, placement: 'top'})
        .on("mouseenter", function () {
            var _this = this;
            $(this).popover("show");
            $(".popover").on("mouseleave", function () {
                $(_this).popover('hide');
            });
        }).on("mouseleave", function () {
        var _this = this;
        setTimeout(function () {
            if (!$(".popover:hover").length) {
                $(_this).popover("hide");
            }
        }, 300);
    });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/***
 * POST or PUT dataset to the Archive API
 *
 * @param submissionObj - dictionary of dataset
 * @param url (default: api/v1/datasets)
 * @param method (default: POST)
 * @returns {jQuery}
 */
function submitDataset(submissionObj, url="api/v1/datasets/", method="POST") {
    var deferObj = jQuery.Deferred();
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    $.ajax({
        method: method,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        url: url,
        dataType: "json",
        data: JSON.stringify(submissionObj),
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function processEditingForm(submissionObj, url) {
    var submitMode = true;

    $('.js-edit-form .js-param.missing').each(function () {
        $(this).removeClass('missing');
    });

    var entryCount = 0;
    //find all the contacts and authors first before processing others
    if ($('.js-new-value.js-input').length > 0) {
        var validEntries = true;

        $('.js-new-value.js-input').each(function (index) {
            if (!$(this).find('.js-first-name').val() || !$(this).find('.js-last-name').val()) {
                validEntries = false;
            }
        });

        if (validEntries) {

            $('.js-edit-form .js-new-value.js-input').each(function (index) {

                var param = $(this).closest('.js-param').attr('data-param');

                var fname = $(this).find('.js-first-name').val();
                var lname = $(this).find('.js-last-name').val();
                var email = $(this).find('.js-email').val();
                var orcid = $(this).find('.js-orcid').val();

                $.when(createContact(fname, lname, email, '', orcid)).done(function(status) {
                    if (status.url && entryCount == $('.js-new-value.js-input').length - 1) {
                        if (!submissionObj[param] && param == 'authors') {
                            submissionObj[param] = [];
                            submissionObj[param].push(status.url);
                        } else if (param == 'contact') {
                            submissionObj[param] = status.url;
                        } else if (param == 'authors') {
                            submissionObj[param].push(status.url);
                        }
                        entryCount++;
                        submissionObj = processForm(submissionObj, submitMode, true);
                        if (submissionObj.submit) {
                            delete submissionObj.submit;
                            $.when(submitDataset(submissionObj, url, method="PUT")).done(function (status) {
                                if (status.result) {
                                    $.when(changeStatus(url, "submit")).always(function (submitStatus) {
                                        if (submitStatus.result && submitStatus.detail) {
                                            alert(submitStatus.detail + 'Please note: The screen will refresh after you click OK.');
                                            $('.js-clear-form').trigger('click');
                                            $('.js-clear-file').trigger('click');
                                        } else {
                                            handleFormErrors(submitStatus, "Dataset submission failed. Please check the fields and try again.");
                                        }
                                    });
                                } else {
                                    handleFormErrors(status, "There was an error with the update.");
                                }
                            });

                        } else {
                            alert('Please check your entries and try again.');
                        }
                    } else if (status.url) {
                        if (!submissionObj[param] && param == 'authors') {
                            submissionObj[param] = [];
                            submissionObj[param].push(status.url);
                        } else if (param == 'contact') {
                            submissionObj[param] = status.url;
                        } else if (param == 'authors') {
                            submissionObj[param].push(status.url);
                        }
                        entryCount++;
                    } else {
                        var responseStr = '';
                        if (status.responseText) {

                            var response = JSON.parse(status.responseText);
                            for (var prop in response) {
                                responseStr += prop + ': ' + response[prop] + '\n';
                            }
                        }
                        alert('There was a problem creating the new entry.\n' + responseStr);
                    }
                });

            });
        } else {
            alert('Please enter first and last names, and email for all new contacts/authors.');
        }
    } else {
        submissionObj = processForm(submissionObj, submitMode, true);
        if (submissionObj.submit) {
            delete submissionObj.submit;
            $.when(submitDataset(submissionObj, url, method="PUT")).done(function (status) {
                if (status.result) {
                    $.when(changeStatus(url, "submit")).always(function (submitStatus) {
                        if (submitStatus.result && submitStatus.detail) {
                            alert(submitStatus.detail + 'Please note: The screen will refresh after you click OK.');
                            $('.js-clear-form').trigger('click');
                            $('.js-clear-file').trigger('click');
                        } else {
                            handleFormErrors(submitStatus, "Dataset submission failed. Please check the fields and try again.");
                        }
                    });
                } else {
                    handleFormErrors(status, "There was an error with the update.");
                }
            });
        } else {
            alert('Please fill in all the required fields.');
            $('body').animate({
                scrollTop: $('.js-edit-form').offset().top
            }, 500);
        }
    }
}

function createContact(fname, lname, email, institute, orcid) {
    var deferObj = jQuery.Deferred();
    var data = {
        "first_name": fname,
        "last_name": lname,
        "email": email,
        "institution_affiliation": institute,
        "orcid": orcid};
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    //data = JSON.stringify(data);
    $.ajax({
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        url: "api/v1/people/",
        dataType: "json",
        data: JSON.stringify(data),
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

/**
 * Change the status of a dataset with the given url
 * @param url
 * @returns {jQuery}
 */
function changeStatus(url, status="submit") {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: url+status,
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });
    return deferObj.promise();
}

function getDataSets(url) {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: (url ? url : "api/v1/datasets/"),
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function getVariables() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/variables/",
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function getSites() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/sites/",
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function getContacts() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/people/",
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function getPlots() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/plots/",
        dataType: "json",
        success: function (data) {
            data.result = true;
            deferObj.resolve(data);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            jqXHR.result = false;
            deferObj.resolve(jqXHR);
        },

    });

    return deferObj.promise();
}

function getFileTypes() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "OPTIONS",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        url: "api/v1/datasets/",
        dataType: "json",
        success: function (data) {
            dataObj.filetypes = data.actions.upload.parameters.attachment.allowed_mime_types;
        },
        fail: function (data) {
            deferObj.resolve(false);
        },

        error: function (data, errorThrown) {
            deferObj.resolve(false);
        },
    });
    return deferObj.promise();
}

function getMetadata(templateType) {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "OPTIONS",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        url: "api/v1/" + templateType + "/",
        dataType: "json",
        success: function (data) {
            deferObj.resolve(data.actions.POST);
        },

        fail: function (jqXHR, textStatus, errorThrown) {
            deferObj.resolve(data);
        },

        error: function (jqXHR, textStatus, errorThrown) {
            deferObj.resolve(data);
        },

    });
    return deferObj.promise();
}

/**
 * Handle the errors in the HTTP Response object returned.
 * This will handle 400 and 500 errors.
 * @param httpResponse
 * @param errorPrefixMessage
 */
function handleFormErrors(httpResponse, errorPrefixMessage) {
    var responseStr = '';

    // if status 400 then collect the errors
    if (httpResponse.status === 400) {
        if (httpResponse.responseText) {

            var response = JSON.parse(httpResponse.responseText);
            for (var prop in response) {

                // Which fields are missing
                if (prop === "missingRequiredFields")
                    for (var i in response.missingRequiredFields) {

                        var field = response.missingRequiredFields[i];
                        responseStr += templates.datasets[field].label + ': Missing \n';
                    }
                else {
                    responseStr += templates.datasets[prop].label + ': ' + response[prop] + '\n';
                }
            }
        }
    }
    alert(errorPrefixMessage + '\n\n' + responseStr);
}