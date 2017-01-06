var dataObj = {};
var templates = {};

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

$(document).ready(function(){
    $(document).foundation();

    $.getJSON( "static/js/metadata/dataset.json", function( data ) {  
        templates.datasets = data;
        //console.log(templates.dataset);
        console.log(data);
        createEditForm('datasets');
    });

    /*$.when(getMetadata('datasets')).done(function(datasetMetadata) {
        templates.datasets = datasetMetadata;
        createEditForm('datasets');
    });*/

    var viewParam = getParameterByName('view', window.location.href);

    if(viewParam && $('.js-view[data-view="' + viewParam + '"]').length == 1) {
        $('.js-view[data-view="' + viewParam + '"]').removeClass('hide');
        $('.js-home-view').addClass('hide');
    }

    var popup = new Foundation.Reveal($('#myModal'));
    console.log('here');

    if($('.js-auth').attr('data-auth') == 'false') {
        window.location = 'api/api-auth/login/?next=/';
    }

    $.when(getContacts()).done(function(contacts) {
        console.log(contacts);
        dataObj.contacts = contacts;
        var contactList = [];
        for(var i=0;i<contacts.length;i++) {
            contactList.push(contacts[i].first_name + ' ' + contacts[i].last_name);
        }

        $( ".js-contacts-widget" ).autocomplete({
          source: contactList
        });/*.autocomplete( "instance" )._renderItem = function( ul, item ) {
          return $( "<li>" )
            .append( "<div>" + item.first_name + " " + item.last_name + "</div>")
            .appendTo( ul );
            console.log('here');
        };*/

        /*$( ".js-contacts-widget" ).autocomplete({
          minLength: 0,
          source: contacts,
          focus: function( event, ui ) {
            $( ".js-contacts-widget" ).val( ui.item.first_name + ui.item.last_name );
            return false;
          },
          select: function( event, ui ) {
            $( ".js-contacts-widget" ).val( ui.item.first_name + ui.item.last_name );
            $( ".js-contact-url" ).val(ui.item.url);
            return false;
          }
        })
        .autocomplete( "instance" )._renderItem = function( ul, item ) {
          return $( "<li>" )
            .append( "<div>" + item.first_name + " " + item.last_name + "</div>")
            .appendTo( ul );
        };*/
    });

    $.when(getSites()).done(function(sites) {
        console.log(sites);
        dataObj.sites = sites;
        for(var i=0;i<sites.length;i++) {
            var option = $('<option value="'+ sites[i].url +'" data-index="' + i + '">' + sites[i].name + ': ' + (sites[i].site_id ?  sites[i].site_id : 'N/A')+ '</option>');
            $('.js-all-sites').append(option);
        }
    });

    $.when(getVariables()).done(function(vars) {
        console.log(vars);
        dataObj.variables = vars;
        for(var i=0;i<vars.length;i++) {
            var option = $('<option value="'+ vars[i].url +'" data-index="' + i + '">' + vars[i].name + ': ' + (vars[i].name ?  vars[i].name : 'N/A')+ '</option>');
            $('.js-all-vars').append(option);
        }
    });

    $.when(getPlots()).done(function(plots) {
        console.log(plots);
        dataObj.plots = plots;
        for(var i=0;i<plots.length;i++) {
            var option = $('<option value="'+ plots[i].url +'" data-index="' + i + '">' + plots[i].name + ': ' + (plots[i].plot_id ? plots[i].plot_id : 'N/A') + '</option>');
            $('.js-all-plots').append(option);
        }
    });

    $('body').on('click', '.js-view-toggle', function(event) {
        var view = $(this).attr('data-view');

        switch(view) {
            case 'create': 
            
            break;

            case 'edit':

            break;

            case 'view':

            break;

            default: break;
        }

        $('.js-view[data-view="' + view + '"]').removeClass('hide');
        window.location = window.location.href + '?view=' + view;
        $('.js-home-view').addClass('hide');
    });

    $('body').on('change', '.js-all-sites', function() {
        //console.log('here');
        var index = $(this).find('option:selected').attr('data-index');
        $('.js-view-site-btn .js-site-id').html($(this).val());
        $('.js-site-info').removeClass('hide');
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
        for(var prop in dataObj.sites[index]) {
            var param = $('<p>' + prop + ': ' + dataObj.sites[index][prop] + '</p>');
            $('.js-params').append(param);
        }
    });

    $('body').on('change', '.js-all-plots', function() {
        //console.log('here');
        var index = $(this).find('option:selected').attr('data-index');
        $('.js-view-plot-btn .js-plot-id').html($(this).val());
        $('.js-plot-info').removeClass('hide');
        $('.js-plot-params').html('');
        for(var prop in dataObj.sites[index]) {
            var param = $('<p>' + prop + ': ' + dataObj.sites[index][prop] + '</p>');
            $('.js-plot-params').append(param);
        }
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

    $(document).on('focus',".datepicker_recurring_start", function(){
        $(this).datepicker();
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
    

    /*$('body').on('click', '.js-file-download-btn', function() {
        var archiveUrl = $(this).attr('data-archive');
        //        https://ngt-dev.lbl.gov/api/v1/datasets/27/archive/
        var csrftoken = getCookie('csrftoken');

        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        });

        $.ajax({
            method: "GET",
            dataType: 'application/json',
            url: archiveUrl,
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
    });*/

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

    $('body').on('click', '.js-clear-form', function() {
        $('.js-param.missing').each(function() {
            $(this).removeClass('missing');
        });
    });

    $('body').on('click', '.js-create-dataset', function() {
        var submissionObj = {};
        var submit = true;

        $('.js-param.missing').each(function() {
            $(this).removeClass('missing');
        });

        $('.js-create-form .js-param').each(function() {
            var param = $(this).attr('data-param');
            var required = $(this).hasClass('required');
            $(this).find('textarea, input[type="text"], select').each(function() {
                if($(this).val() != null) {
                    if($(this).val().trim()) {
                        submissionObj[param] = $(this).val().trim();
                    }
                }
                //hold off on implementing required for now
                /*else if (required && !$(this).val().trim()) {
                    submit = false;
                    $(this).closest('.js-param').addClass('missing');
                }*/
            });
        });

        console.log(submissionObj);

        if(submit) {

            $.when(createDataset(submissionObj)).done(function(status) {
                if(status) {
                    alert('Dataset successfully created.');
                }
                else {
                    alert('There was an error. Please try again later.');
                }

                $('.js-clear-form').trigger('click');
            });

        }
        else {
            alert('Please fill in the missing fields');
            $('body').animate({
                scrollTop: $('.js-create-form').offset().top
            }, 500);
        }
        
    });

    $('body').on('click', '.js-edit-dataset-btn', function() {
        //$('')
        $('.js-edit-form').removeClass('hide');
        $('.js-display-section').addClass('hide');
    });

    $('body').on('click', '.js-save-dataset', function() {
        var url = $('.js-edit-form').attr('data-url');
        var submissionObj = {};
        $('.js-edit-form .js-param').each(function() {
            var param = $(this).attr('data-param');
            if($(this).find('.js-input').length == 1) {
                var value = $(this).find('.js-input').val();
                if(value) {
                    submissionObj[param] = value;
                }
            }
            else if($(this).find('.js-input').length > 1) {
                var value = [];
                $(this).find('.js-input').each(function() {
                    if($(this).val().trim()) {
                        value.push($(this).val().trim());
                    }
                });
                if(value.length > 0) {
                    submissionObj[param] = value;
                }
            }
        });

        console.log(submissionObj);

        $.when(editDataset(submissionObj, url)).done(function(data) {
            console.log(data);
        });
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
                                .append('<button class="js-view-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">View</button>')
                                .append('&nbsp;' + '<button class="js-delete-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">Delete</button>' + '<br><br>');
            }
        });
    });

    $('body').on('click', '.js-view-dataset', function() {
        var index = $(this).attr('data-index');
        var url = $(this).attr('data-url');

        $.when(getDataSets(url)).done(function(datasetObj) {
            console.log(datasetObj);
            $('#myModal #modalTitle').html('')
                                    .html(dataObj.datasets[index]['name']);
            $('#myModal .js-modal-body').html('');
                var inputString = '';
                var editForm = $('.js-create-form.dataset').clone()
                        .attr('data-url', url)
                        .addClass('hide')
                        .removeClass('js-create-form')
                        .addClass('js-edit-form');
                editForm.find('.js-create-dataset').addClass('hide');
                editForm.find('.js-save-dataset').removeClass('hide');
                editForm.find('.js-input.date').attr('id', '');
                $('#myModal .js-modal-body').append(editForm);
                $('.js-input.date').datepicker({
                    dateFormat: "yy-mm-dd"
                });
                
                for(var prop in datasetObj) {
                    if(!templates.datasets[prop].read_only) {
                        var substring = '<b class="js-param-name">' + templates.datasets[prop].label + '</b>:' + '&nbsp;';
                        substring += '&nbsp;<span class="js-param-val">' + datasetObj[prop] + '</span><br>';
                        $('#myModal .js-modal-body').append($('<div/>').append(substring).addClass('js-display-section'));
                    }
                    if(Array.isArray(datasetObj[prop]) && datasetObj[prop].length > 1) {
                        var position = $('.js-edit-form .' + prop).find('.js-input');
                        for(var j=0; j < datasetObj[prop].length - 1; j++) {
                            $('.js-edit-form .' + prop).find('.js-input').clone().insertAfter(position);
                        }
                        for(var k=0;k<datasetObj[prop].length;k++) {
                            $($('.js-edit-form .' + prop).find('.js-input')[k]).val(datasetObj[prop][k]);
                        }
                    }
                    else {
                        $('.js-edit-form .' + prop).find('.js-input').val(datasetObj[prop]);
                    }
                }
                
                $('#myModal .js-save-btn').attr('data-url', dataObj.datasets[index]['url'])
                                        .attr('data-id', dataObj.datasets[index]['data_set_id']);
                $('#myModal .js-file-download-btn').attr('data-url', dataObj.datasets[index]['url'])
                                        .attr('data-archive', dataObj.datasets[index]['archive'])
                                        .attr('href', dataObj.datasets[index]['archive']);

            //}

            popup.open();
        });
    
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

function populateDatasets(filter, container) {

}

function createEditForm(templateType) {
    var formHTML = $('<div/>');
    var paramHTML = '';
    for(var param in templates[templateType]) {
        /*paramHTML = $('<div class="js-param param"></div>');
        paramHTML.append($('<span class="js-display-name display-name"></span>').html(templates[templateType][param].display_name));
        paramHTML.append($('.js-template' + '.' + templates[templateType][param].datatype).clone());
        $(formHTML).append(paramHTML);
        if(templates[templateType][param].multiple == 1) {
            $(formHTML).append('<button class="js-add-param-btn button '+ templates[templateType][param].datatype + '">' + 'Add New' + '</button>');
        }*/
        if(templates[templateType][param].read_only) {
            paramHTML = $('<input type="hidden">').addClass(param + (templates[templateType][param].required ? "required" : "") + ' js-param')
                                                .val(templates[templateType][param].value)
                                                .attr('data-param', param);
        }
        else {
            paramHTML = $('<div class="js-param ' + (templates[templateType][param].required ? 'required' : '') + ' param"></div>').addClass(param)
                        .attr('data-param', param);
            var label = templates[templateType][param].label;
            if(templates[templateType][param].required) {
                label += '<i class="required">*</i>';
            }
            paramHTML.append($('<span class="js-display-name display-name"></span>').html(label + '&nbsp;'));
            switch(templates[templateType][param].type) {
                case "string":
                var tag = $('.js-template' + '.' + templates[templateType][param].type).clone();
                if(templates[templateType][param].max_length) {
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
                tag.removeClass('js-template').addClass('js-input');
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
                //var tag = $();
                console.log(list);
                $('.js-ref-list[data-list="' + list + '"]').clone().removeClass('hide').appendTo(paramHTML);
                break;

                default:
                var tag = $('<textarea/>').addClass('js-input');
                paramHTML.append(tag);
                break;
            }
            
        }

        $(formHTML).append(paramHTML);
    }
    $('.js-create-form').prepend(formHTML);
    $('.js-input.date').datepicker({
        dateFormat: "yy-mm-dd"
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

function createDataset(submissionObj) {
    var deferObj = jQuery.Deferred();
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
        url: "api/v1/people/",
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

function getDataSets(url) {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: (url ? url : "api/v1/datasets/"),
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
        url: "api/v1/people/",
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

function getMetadata(templateType) {
    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "OPTIONS",
        headers: { 
            'Accept': 'application/json',
            'Content-Type': 'application/json' 
        },
        url: "api/v1/"+templateType+"/",
        dataType: "json",
        success: function(data) {
            console.log(data.actions.POST);
            deferObj.resolve(data.actions.POST);
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
