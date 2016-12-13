var dataObj = {};
var templates = {};
$(document).ready(function(){
    $(document).foundation();

    $.getJSON( "/static/js/metadata/dataset.json", function( data ) {  
        templates.dataset = data;
        //console.log(templates.dataset);
        console.log(data);
        createEditForm('dataset');
    });

    var popup = new Foundation.Reveal($('#myModal'));
    console.log('here');

    if($('.js-auth').attr('data-auth') == 'false') {
        window.location = '/api/api-auth/login/?next=/';
    }

    $('.js-template.date').datepicker({
        dateFormat: "yy-mm-dd"
    });

    /*$.when(getDataSets()).then(function(data) {
        console.log(data);
        for(var i=0;i<data.length;i++) {
            $('main').append('<p>' + data[i].dataSetId + '</p>');
            $('main').append('<p>' + data[i].description + '</p>');
        }
    });

    $.when(getVariables()).then(function(data) {
        console.log(data);
        for(var i=0;i<data.length;i++) {
            $('main').append('<p>' + data[i].name + '</p>');
        }
    });

    $.when(getSites()).then(function(data) {
        console.log(data);
        for(var i=0;i<data.length;i++) {
            $('main').append('<p>' + data[i].name + '<br>')
                .append(data[i].siteId + '<br>')
                .append(data[i].description + '<br>')
                .append(data[i].country + '<br>')
                .append(data[i].stateProvince + '<br>')
                .append(data[i].utcOffset + '<br>')
                .append(data[i].locationLatitude + '<br>')
                .append(data[i].locationLongitude + '<br>')
                .append(data[i].locationElevation + '<br>')
                .append(data[i].locationMapUrl + '<br>')
                .append(data[i].locationBoundingBoxUlLatitude + '<br>')
                .append(data[i].locationBoundingBoxUlLongitude + '<br>')
                .append(data[i].locationBoundingBoxLrLatitude + '<br>')
                .append(data[i].locationBoundingBoxLrLongitude + '<br>')
                .append(data[i].siteUrls + '<br>')
                .append(data[i].submissionDate + '<br>')
                .append(data[i].submission + '<br></p>');
        }
    });

    $.when(getContacts()).then(function(data) {
        console.log(data);
        for(var i=0;i<data.length;i++) {
            $('main').append('<p>' + data[i].firstName + '<br>')
                    .append(data[i].lastName + '<br>')
                    .append(data[i].email + '<br>')
                    .append(data[i].institutionAffiliation + '<br></p>');
        }
    });

    $.when(getPlots()).then(function(data) {
        console.log(data);
        for(var i=0;i<data.length;i++) {
            $('main').append('<p>' + data[i].plotId + '<br>')
                    .append(data[i].name + '<br>')
                    .append(data[i].description + '<br>')
                    .append(data[i].size + '<br>')
                    .append(data[i].locationElevation + '<br>')
                    .append(data[i].locationKmzUrl + '<br>')
                    .append(data[i].submissionDate + '<br>')
                    .append(data[i].pi + '<br>')
                    .append(data[i].site + '<br>')
                    .append(data[i].submission + '<br></p>');
        }
    });*/


    $('body').on('click', '.js-file-upload-btn', function() {
        $('.js-file-input-btn').trigger('click');
    });

    $('body').on('change', '.js-file-input-btn', function() {
        var dataFile = this.files[0];
        var dataSetId = $('.js-upload-dataset-id').val();

        if(!dataSetId) {
            alert('Please enter a dataset ID to test the upload');
        }

        else {
            if(dataFile.name.split('.').pop() == 'zip' || dataFile.type.indexOf('zip') != -1) {
                //alert('Valid file');
                var csrftoken = getCookie('csrftoken');

                $.ajaxSetup({
                    beforeSend: function(xhr, settings) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                });

                var data = {
                    attachment: this.files
                };

                var formData = new FormData();
                formData.append('attachment', this.files[0]);

                //data = JSON.parse(data);

                $.ajax({
                    method: "POST",
                    contentType: false,
                    data: formData,
                    processData: false,
                    url: "api/v1/datasets/" + dataSetId + "/upload/",
                    success: function(data) {
                        alert('Success');
                    },

                    fail: function(data) {
                        var detailObj = JSON.parse(data.responseText);
                        alert('Fail: ' + detailObj.detail);
                    },

                    error: function(data, errorThrown) {
                        var detailObj = JSON.parse(data.responseText);
                        alert('Fail: ' + detailObj.detail);
                    },

                });

            }
            else {
                alert('Invalid file format. Please upload a zip file');
            }
        }
        //console.log(this);
    });    


    $('body').on('click', '.js-delete-dataset', function() {
        var csrftoken = getCookie('csrftoken');
        var url = $(this).attr('data-url');

        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
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
            success: function(data) {
                alert('Dataset deleted');
            },

            fail: function(data) {
                alert('Fail');
            },

            error: function(data, errorThrown) {
                alert('Error: ' + data.statusText);
            },
        });
    });

    $('body').on('click', '.js-save-btn', function() {
        var url = $(this).attr('data-url');
        var id = $(this).attr('data-id');

        var jsonObj = {};

        $('.js-editable-section .js-attr').each(function() {
            var attr = $(this).find('.js-attr-name').html();
            if($(this).find('.js-attr-val').length > 1) {
                jsonObj[attr] = [];
                $(this).find('.js-attr-val').each(function() {
                    jsonObj[attr].push($(this).val());
                });

            }
            else if($(this).find('.js-attr-val').length == 1) {
                jsonObj[attr] = $(this).find('.js-attr-val').val();
            }
            else if($(this).find('.js-attr-val').length == 0) {
                jsonObj[attr] = "";
            }

        });
        console.log(jsonObj);
        $.when(editDataset(jsonObj, url)).done(function(status) {
            if(status) {
                alert('Your changes have been saved');
            }
            else {
                alert('Fail');
            }
        });

        
    })

    $('body').on('click', '.js-create-dataset', function() {
        var status = createDataset($('.js-dataset-name').val(), $('.js-dataset-desc').val());
        if(status) {
            alert('Dataset successfully created');
        }
        else {
            alert('Fail');
        }

        $('.js-clear-form').trigger('click');
    });

    $('body').on('click', '.js-create-contact', function() {
        var status = createContact($('.js-contact-fname').val(), $('.js-contact-lname').val(), $('.js-contact-email').val(), $('.js-contact-institute').val());
        if(status) {
            alert('Contact successfully created');
        }
        else {
            alert('Fail');
        }
    });

    $('body').on('click', '.js-get-datasets', function() {
        $.when(getDataSets()).then(function(data) {
            dataObj.datasets = data;
            //console.log(data);
            $('.js-text-dump').html('');
            $('.js-datasets').html('');
            for(var i=0;i<data.length;i++) {
                $('.js-text-dump').append('Name: ' + (data[i].name ? data[i].name : 'NA') + '<br>')
                                .append('Description: ' + (data[i].description ? data[i].description : 'NA') + '<br><br>');

                $('.js-datasets').append('Name: ' + (data[i].name ? data[i].name : 'NA') + '<br>')
                                .append('Description: ' + (data[i].description ? data[i].description : 'NA') + '<br>')
                                .append('<button class="js-view-dataset button" data-id="' + data[i].dataSetId + '" data-index="' + i + '">View</button>' + '<br><br>');
            }
        });
    });

    $('body').on('click', '.js-view-dataset', function() {
        var index = $(this).attr('data-index');
        
        $('#myModal #modalTitle').html('')
                                .html(dataObj.datasets[index]['name']);
        $('#myModal .js-modal-body').html('');
        //if(dataObj.datasets[index].dataSetId == $(this).attr('data-id')) {

            var inputString = '';
            //inputString += 'Name: ' + '<input type="text" class="js-dataset-name" value="' + dataObj.datasets[index]['name'] + '">' + '<br>';
            //inputString += 'Description: ' + '<textarea class="js-dataset-desc">' + dataObj.datasets[index]['description'] + '</textarea>';

            for(var prop in dataObj.datasets[index]) {
                if(dataObj.datasets[index][prop] == null) {
                    inputString += '<div class="js-attr"><span class="js-attr-name ' + prop + '">' + prop + '</span><br>' + '<textarea class="' + prop + ' js-attr-val">' + '</textarea>' + '</div>';
                    $('#myModal .js-modal-body').append('<b>' + prop + '</b>: ' + '' + '<br>');
                }

                else if(typeof dataObj.datasets[index][prop] == 'object') {

                    var substring = '<b>' + prop + '</b>:<br>';
                    inputString += '<div class="js-attr"><span class="js-attr-name ' + prop + '">' + prop + '</span><br>';
                    for(var subprop in dataObj.datasets[index][prop]) {
                        if(dataObj.datasets[index][prop][subprop] == null) {
                            console.log('null');
                        }
                        

                        substring += '&nbsp;&nbsp;' + dataObj.datasets[index][prop][subprop] + '<br>';
                        inputString += '&nbsp;&nbsp;' + '<textarea class="' + prop + ' js-attr-val">' + dataObj.datasets[index][prop][subprop] + '</textarea>' + '<br>';
                        $('#myModal .js-modal-body').append(substring);
                    }
                    inputString += '</div>';
                }
                else {
                    inputString += '<div class="js-attr"><span class="js-attr-name ' + prop + '">' + prop + '</span><br>' + '<textarea class="' + prop + ' js-attr-val">' + dataObj.datasets[index][prop] + '</textarea>' + '</div>';
                    $('#myModal .js-modal-body').append('<b>' + prop + '</b>: ' + dataObj.datasets[index][prop] + '<br>');
                }
            }


            $('#myModal .js-editable-section').append(inputString);
            $('#myModal .js-save-btn').attr('data-url', dataObj.datasets[index]['url'])
                                    .attr('data-id', dataObj.datasets[index]['dataSetId']);
        //}
        popup.open();
    
    });

    $('body').on('click', '.js-close-modal', function() {
        popup.close();
    });

    $('body').on('click', '.js-get-sites', function() {
        $.when(getSites()).then(function(data) {
            dataObj.sites = data;
            $('.js-text-dump').html('');
            for(var i=0;i<data.length;i++) {
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
   
    $('body').on('click', '.js-get-plots', function() {
        $.when(getPlots()).then(function(data) {
            dataObj.plots = data;
            $('.js-text-dump').html('');
            for(var i=0;i<data.length;i++) {
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

});

function createEditForm(templateType) {
    var formHTML = $('<div/>');
    var paramHTML = '';
    for(var param in templates[templateType]) {
        paramHTML = $('<div class="js-param param"></div>');
        paramHTML.append($('<span class="js-display-name display-name"></span>').html(templates[templateType][param].display_name));
        paramHTML.append($('.js-template' + '.' + templates[templateType][param].datatype).clone());
        $(formHTML).append(paramHTML);
        if(templates[templateType][param].multiple == 1) {
            $(formHTML).append('<button class="js-add-param-btn button '+ templates[templateType][param].datatype + '">' + 'Add New' + '</button>');
        }
    }
    $('.js-edit-form').append(formHTML);
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

function createDataset(name, desc) {
    var deferObj = jQuery.Deferred();
    var data = { dataSetId: name,
        description: desc };
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
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
        url: "api/v1/datasets/",
        dataType: "json",
        data: JSON.stringify(data),
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(data);
        },

        error: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(data);
        },

    });

    return deferObj.promise();
}

function editDataset(submissionObj, url) {
    var deferObj = jQuery.Deferred();
    /*var data = {
        name: "bla 3454 768 h",
        description: "b76 90 57ah" };
   /* var data = {"data_set_id":"FooBarBaz",
                "description":"A FooBarBaz DataSet",
                "name": "Data Set 1", 
                "status_comment": "",
                "doi": "",
                "start_date": "2016-10-28",
                "end_date": null,
                "qaqc_status": null,
                "qaqc_method_description": "",
                "ngee_tropics_resources": true,
                "funding_organizations": "",
                "doe_funding_contract_numbers": "",
                "acknowledgement": "",
                "reference": "",
                "additional_reference_information": "",
                "additional_access_information": "",
                "submission_date": "2016-10-28T19:12:35Z",
                "contact": "http://testserver/api/v1/people/4/",
                "authors": ["http://testserver/api/v1/people/1/"],
                "sites": ["http://testserver/api/v1/sites/1/"],
                "plots": ["http://testserver/api/v1/plots/1/"],
                "variables": ["http://testserver/api/v1/variables/1/", 
                "http://testserver/api/v1/variables/2/"]};*/
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    //data = JSON.stringify(data);
    $.ajax({
        method: "PUT",
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'application/json' 
        },
        url: url,
        dataType: "json",
        data: JSON.stringify(submissionObj),
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(false);
        },

        error: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(false);
        },

    });

    return deferObj.promise();
}

function createContact(fname, lname, email, institute) {
    var deferObj = jQuery.Deferred();
    var data = { "firstName": fname,
        "lastName": lname,
        "email": email,
        "institutionAffiliation": institute };
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
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
        url: "api/v1/contacts/",
        dataType: "json",
        data: JSON.stringify(data),
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(data);
        },

        error: function(jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
            deferObj.resolve(data);
        },

    });

    return deferObj.promise();
}

function getDataSets() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/datasets/",
        dataType: "json",
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            console.log(data);
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            console.log(data);
            deferObj.resolve(data);
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
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            console.log(data);
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            console.log(data);
            deferObj.resolve(data);
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
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            console.log(data);
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            console.log(data);
            deferObj.resolve(data);
        },

    });

    return deferObj.promise();    
}

function getContacts() {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: "api/v1/contacts/",
        dataType: "json",
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            console.log(data);
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            console.log(data);
            deferObj.resolve(data);
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
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            console.log(data);
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            console.log(data);
            deferObj.resolve(data);
        },

    });

    return deferObj.promise();    
}