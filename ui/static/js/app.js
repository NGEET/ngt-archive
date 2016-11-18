$(document).ready(function(){
    console.log('here');

    if($('.js-auth').attr('data-auth') == 'false') {
        window.location = '/api/api-auth/login/?next=/';
    }

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
            //console.log(data);
            $('.js-text-dump').html('');
            for(var i=0;i<data.length;i++) {
                $('.js-text-dump').append('ID: ' + (data[i].dataSetId ? data[i].dataSetId : 'NA') + '<br>')
                                .append('Description: ' + (data[i].description ? data[i].description : 'NA') + '<br><br>');
            }
        });
    });

    $('body').on('click', '.js-get-sites', function() {
        $.when(getDataSets()).then(function(data) {
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
        $.when(getDataSets()).then(function(data) {
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