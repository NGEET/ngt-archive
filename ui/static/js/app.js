var dataObj = {};
var templates = {};
var fileToUpload = '';

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
  var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
  '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.?)+[a-z]{2,}|'+ // domain name
  '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
  '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
  '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
  '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
  return pattern.test(str);
}

function fileTypeAllowed(filetype) {
    for(var i=0;i<dataObj.filetypes.length;i++) {
        if(dataObj.filetypes[i].indexOf(filetype) !=-1) {
            return dataObj.filetypes[i].indexOf(filetype);
        } 
    }

    return -1;
}

$(document).ready(function(){
    $(document).foundation();

    if($('.js-auth').attr('data-auth') == 'false') {
        window.location = 'api/api-auth/login/?next=/';
    }
    else if($('.js-auth').attr('data-auth') == 'fluxnet') {
        $('.js-main-article').addClass('hide');
        $('.js-error-article').removeClass('hide');
    }

    $.getJSON( "static/js/metadata/dataset.json", function( data ) {  
        templates.datasets = data;
        //console.log(templates.dataset);
        //console.log(data);
        createEditForm('datasets');
    });

    $.getJSON( "static/js/metadata/site.json", function( data ) {  
        templates.sites = data;
        
    });

    $.getJSON( "static/js/metadata/plot.json", function( data ) {  
        templates.plots = data;
        
    });    

    /*$.when(getMetadata('datasets')).done(function(datasetMetadata) {
        templates.datasets = datasetMetadata;
        createEditForm('datasets');
    });*/

    var viewParam = getParameterByName('view', window.location.href);

    if(viewParam && $('.js-view[data-view="' + viewParam + '"]').length == 1) {
        $('.js-loading').removeClass('hide');
        $('.js-view[data-view="' + viewParam + '"]').removeClass('hide');
        $('.js-home-view').addClass('hide');
    }

    switch(viewParam) {
        case 'create': 
        $('.js-loading').addClass('hide');
        break;

        case 'edit':
        $('.js-loading').addClass('hide');
        break;

        case 'view-sites':
        $('.js-loading').addClass('hide');
        break;

        case 'edit-draft':
        $.when(getDataSets()).then(function(data) {
            dataObj.datasets = data;
            //console.log(data);
            $('.js-text-dump').html('');
            $('.js-datasets').html('');
            for(var i=0;i<data.length;i++) {
                if(data[i].status == 0) {
                    var tag = $('<div/>').addClass('js-view-dataset dataset');
                    tag.append('<h5 class="title">' + (data[i].name ? data[i].name : 'NA') + '</h5>')
                        .append('<p class="desc">' + (data[i].description ? data[i].description.substring(0, 199) + '...' : 'NA') + '</p>')
                        .append('<button class="button js-edit-draft">Edit</button>')
                        .attr('data-url', data[i].url)
                        .attr('data-index', i);

                    $('.js-all-datasets').append(tag);   

                    /*$('.js-all-datasets').append((data[i].name ? data[i].name : 'NA') + '<br>')
                                    .append((data[i].description ? data[i].description : 'NA') + '<br>')
                                    .append('<button class="js-view-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">View</button>')
                                    .append('&nbsp;' + '<button class="js-delete-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">Delete</button>' + '<br><br>');*/
                }
            }
            $('.js-loading').addClass('hide');
        });
        break;

        case 'view':
        //$('.js-get-datasets').trigger('click');
        $.when(getDataSets()).then(function(data) {
            dataObj.datasets = data;
            //console.log(data);
            $('.js-text-dump').html('');
            $('.js-datasets').html('');
            for(var i=0;i<data.length;i++) {
                
                if(data[i].status == 2) {
                    var tag = $('<div/>').addClass('js-view-dataset dataset');
                    tag.append('<h5 class="title">' + (data[i].name ? data[i].name : 'NA') + '</h5>')
                        .append('<p class="desc">' + (data[i].description ? data[i].description.substring(0, 199) + '...' : 'NA') + '</p>')
                        .attr('data-url', data[i].url)
                        .attr('data-index', i);

                    switch(data[i].status) {
                        case '0': 
                            tag.find('.title').append('<span class="tag draft">Draft</span>');
                            break;

                        case '1': 
                            tag.find('.title').append('<span class="tag submitted">Submitted</span>');
                            break;

                        case '2':
                            tag.find('.title').append('<span class="tag approved">Approved</span>');
                            break;
                    }

                    $('.js-all-datasets').append(tag); 
                }              
                    /*$('.js-all-datasets').append((data[i].name ? data[i].name : 'NA') + '<br>')
                                    .append((data[i].description ? data[i].description : 'NA') + '<br>')
                                    .append('<button class="js-view-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">View</button>')
                                    .append('&nbsp;' + '<button class="js-delete-dataset button" data-url="' + data[i].url + '" data-index="' + i + '">Delete</button>' + '<br><br>');*/
                
            }
            $('.js-loading').addClass('hide');
        });
        break;

        default: break;
    }


    var popup = new Foundation.Reveal($('#myModal'));
    getFileTypes();

    console.log('here');

    $.when(getContacts()).done(function(contacts) {
        console.log(contacts);
        dataObj.contacts = contacts;
        var contactList = [];

        $('.js-all-contacts').append('<option value="add-new" data-index="-1" class="add-new-option"> - Add New Entry - </option>');
        for(var i=0;i<contacts.length;i++) {
            var option = $('<option value="'+ contacts[i].url +'" data-index="' + i + '">' + contacts[i].first_name + ' ' + contacts[i].last_name + '</option>');
            $('.js-all-contacts').append(option);
        }

        //var addNewInput = $('<div class="js-input js-new-value"><><input type="text" class="hide" placeholder="First Name">');

        //addNewInput.insertAfter('.js-all-contacts');
        /*for(var i=0;i<contacts.length;i++) {
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
            var option = $('<option value="'+ sites[i].url +'" data-index="' + i + '">' + sites[i].site_id + ': ' + sites[i].name + '</option>');
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
            var option = $('<option value="'+ plots[i].url +'" data-index="' + i + '">' + (plots[i].plot_id ? plots[i].plot_id : 'N/A') + ': ' + plots[i].name + '</option>');
            $('.js-all-plots').append(option);
        }
    });

    $('body').on('click', '.js-view-toggle', function(event) {
        var view = $(this).attr('data-view');
        $('.js-view[data-view="' + view + '"]').removeClass('hide');
        window.location = window.location.href + '?view=' + view;
        $('.js-home-view').addClass('hide');
    });

    $('body').on('change', '.js-all-sites', function() {
        //console.log('here');
        var plotTitle = false;
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
        $('.js-site-info .js-title').html('').append('<h4>' + dataObj.sites[index]['site_id'] + ': ' + dataObj.sites[index]['name'] + '</h4>');
        for(var prop in dataObj.sites[index]) {
            if(prop != 'site_id' && prop != 'name') {
                
                if(prop == 'description') {
                    var param = $('<div>' + dataObj.sites[index][prop] + '</div>');
                    $('.js-main-params').append(param);
                }
                else {
                    var param = $('<div class="row param ' + ((templates.sites[prop] && templates.sites[prop].sequence === -1) ? 'hide' : '') +'"> <div class="columns small-12 medium-3">'  +'<b>' + (templates.sites[prop] ? templates.sites[prop].label : prop) + ' </b></div></div>');
                    if(prop == 'contacts') {
                        for(var i=0;i<dataObj.contacts.length;i++) {
                            if(dataObj.sites[index][prop].indexOf(dataObj.contacts[i].url) != -1) {
                                param.append('<div class="columns small-12 medium-9 end float-right">' + dataObj.contacts[i].first_name + ' ' + dataObj.contacts[i].last_name + '</div>');
                            }
                        }
                    }
                    else if(prop == 'pis') {
                        for(var j=0;j<dataObj.contacts.length;j++) {
                            if(dataObj.sites[index][prop].indexOf(dataObj.contacts[j].url) != -1) {
                                param.append('<div class="columns small-12 medium-9 end float-right">' + dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name + '</div>');
                            }
                        }
                    }
                    else if(prop == 'site_urls' || prop == 'location_map_url') {
                        param.append('<div class="columns small-12 medium-9 end float-right">' + '<a href="' + dataObj.sites[index][prop] + '">' + (dataObj.sites[index][prop] ? 'Click here' : '') + '</a>' + '</div>');
                    }
                    else {
                        param.append('<div class="columns small-12 medium-9">' + (dataObj.sites[index][prop] ? dataObj.sites[index][prop] : 'N/A') + '</div>');
                    }
                    $('.js-params').append(param);
                }
            }
        }

        for(var i=0; i< dataObj.plots.length; i++) {
            if(dataObj.plots[i].site == dataObj.sites[index].url) {
                if(!plotTitle) {
                    plotTitle = true;
                    $('.js-params').append('<h4 class="plot-title">Plots in ' + dataObj.sites[index].site_id + '</h4>');
                }
                var plotContainer = $('<div class="plot-info js-plot-info"/>');
                plotContainer.append('<h5>' + dataObj.plots[i].plot_id + ': ' + dataObj.plots[i].name + '</h5>');

                for(var prop in dataObj.plots[i]) {
                    if(prop != 'plot_id' && prop != 'name') {
                        if(prop == 'pi') {
                            for(var j=0;j<dataObj.contacts.length;j++) {
                                if(dataObj.plots[i][prop].indexOf(dataObj.contacts[j].url) != -1) {
                                    var param = $('<div class="row param '+ (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') +'"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns">' + dataObj.contacts[j].first_name + ' ' + dataObj.contacts[j].last_name + '</div></div>');
                                    plotContainer.append(param);
                                }
                            }
                        }
                        else if(prop == 'location_kmz_url') {
                            var param = $('<div class="row param '+ (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') +'"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns"><a href="' + dataObj.plots[i][prop] + '">' + (dataObj.plots[i][prop] ? 'Click here' : '') + '</a></div></div>');
                            plotContainer.append(param);
                        }
                        else {
                            var param = $('<div class="row param '+ (templates.plots[prop] && templates.plots[prop].sequence === -1 ? 'hide' : '') +'"><div class="columns small-12 medium-3"><b>' + (templates.plots[prop] ? templates.plots[prop].label : prop) + ' </b></div><div class="small-12 medium-9 columns">' + (dataObj.plots[i][prop] ? dataObj.plots[i][prop] : '') + '</div></div>');
                            plotContainer.append(param);
                        }
                    }
                }
                $('.js-params').append(plotContainer);
            }

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

    $('body').on('change', '.js-all-contacts', function() {
        if($(this).val() == 'add-new') {
            $(this).closest('select').removeClass('js-input');
            $(this).closest('select').siblings('.js-new-value').removeClass('hide').addClass('js-input');
        }
        else {
            $(this).closest('select').addClass('js-input');
            $(this).closest('select').siblings('.js-new-value').addClass('hide').removeClass('js-input');
        }
    });

    /*$('body').on('drop', function(event) {
        //event.preventDefault();
        var files = event.originalEvent.dataTransfer.files;
        $('.js-file-input-btn').value(files[0]);
        $('.js-file-name').html(files[0].name);
        $('.js-file-name-wrapper').removeClass('hide');
        console.log(files[0].name);
    });*/

    $("html").on("dragover", function(event) {
        event.preventDefault();  
        event.stopPropagation();
    });

    $("html").on("dragleave", function(event) {
        event.preventDefault();  
        event.stopPropagation();
    });

    $("html").on("drop", '.js-file-drop-zone',function(event) {
        event.preventDefault();  
        event.stopPropagation();
        var files = event.originalEvent.dataTransfer.files;
        //$('.js-file-input-btn').val(files[0]);
        $('.js-file-name').html(files[0].name);
        $('.js-file-name-wrapper').removeClass('hide');
        fileToUpload = files[0];
        console.log(files[0]);
    });

    $('body').on('click', '.js-clear-file-btn', function(event) {
        event.preventDefault();
        $('.js-file-input-btn').val('');
        $('.js-file-name').html('')
        $('.js-file-name-wrapper').addClass('hide');
    });

    $('body').on('click', '.js-edit-draft', function(event) {
        event.preventDefault();
        event.stopPropagation();
        var url = $(this).closest('.js-view-dataset').attr('data-url');
        var index = $(this).closest('.js-view-dataset').attr('data-index');
        
        for(var param in dataObj.datasets[index]) {
            if(Array.isArray(dataObj.datasets[index][param])) {
                console.log('arr');
                for (var i = 0; i < dataObj.datasets[index][param].length; i++) {
                    if(i > 0 ) {
                        var position = $('.js-edit-form .js-param[data-param="'+ param +'"] section').last();
                        var container = position.clone();
                        container.find('.js-input').val(dataObj.datasets[index][param][i]);
                        container.insertAfter(position);
                    }
                    else {
                        $('.js-edit-form .js-param[data-param="'+ param +'"] .js-input').val(dataObj.datasets[index][param][i]);
                    }
                }
            }
            else {
                if($('.js-edit-form .js-param[data-param="'+ param +'"] .js-input').hasClass('switch-input')) {
                    $('.js-edit-form .js-param[data-param="'+ param +'"] .js-input').prop('checked', dataObj.datasets[index][param]);
                }   
                else {
                    $('.js-edit-form .js-param[data-param="'+ param +'"] .js-input').val(dataObj.datasets[index][param]);
                }
            }
        }
        $('.js-edit-form').attr('data-url', url);
        $('.js-view.view-drafts-view .js-all-datasets').addClass('hide');
        $('.js-edit-form').removeClass('hide');
        $('.js-edit-form .js-edit-dataset').removeClass('hide');
        $('.js-edit-form .js-create-dataset').addClass('hide');
        $('.js-edit-form .js-clear-form').addClass('hide');
        $('.js-edit-form .js-cancel-btn').removeClass('hide');
        $('.js-edit-form .js-file-drop-zone').addClass('hide');

        /*$('.js-edit-form .js-param').each(function() {
            var param = $(this).attr('data-param');
            $(this).find('.js-input').val(dataObj.datasets[index][param]);
        });*/
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


    $('body').on('click', '.js-file-upload-btn', function(event) {
        event.preventDefault();
        $('.js-file-input-btn').trigger('click');
    });

    $(document).on('focus',".datepicker_recurring_start", function(){
        $(this).datepicker();
    });

    $('body').on('change', '.js-file-input-btn', function(event) {
        event.preventDefault();
        var dataFile = this.files[0];
        fileToUpload = this.files[0];
        $('.js-file-name').html(this.files[0].name);
        $('.js-file-name-wrapper').removeClass('hide');
        //console.log(this);
    });    
    

    /*$('body').on('click', '.js-file-download-btn', function(event) {
        event.preventDefault();
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

    $('body').on('click', '.js-delete-dataset', function(event) {
        event.preventDefault();
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

    $('body').on('click', '.js-cancel-btn', function(event) {
        event.preventDefault();
        location.reload();
    })

    $('body').on('click', '.js-save-btn', function(event) {
        event.preventDefault();
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

    $('body').on('click', '.js-clear-form', function(event) {
        event.preventDefault();
        location.reload();
        /*$('.js-create-form .js-input').each(function() {
            $(this).val('');
        });

        $('.js-param.missing').each(function() {
            $(this).removeClass('missing');
        });*/
    });

    $('body').on('click', '.js-create-dataset', function(event) {
        event.preventDefault();
        var submissionObj = {};
        submissionObj.submit = true;
        var submitMode = false;

        if($(this).hasClass('js-submit')) {
            submitMode = true;
        }

        $('.js-param.missing').each(function() {
            $(this).removeClass('missing');
        });

        var entryCount = 0;
        //find all the contacts and authors first before processing others
        if($('.js-new-value.js-input').length > 0) {
            var validEntries = true;

            $('.js-new-value.js-input').each(function(index) {
                if(!$(this).find('.js-first-name').val() || !$(this).find('.js-last-name').val()) {
                    validEntries = false;
                }
            });

            if(validEntries) {

                $('.js-new-value.js-input').each(function(index) {

                    var param = $(this).closest('.js-param').attr('data-param');

                    var fname = $(this).find('.js-first-name').val();
                    var lname = $(this).find('.js-last-name').val();

                    $.when(createContact(fname, lname, '', '')).done(function(status) {
                        //console.log(status);
                        if(status.url && entryCount == $('.js-new-value.js-input').length - 1) {
                            if(!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            }
                            else if(param == 'contact') {
                                submissionObj[param] = status.url;
                            }
                            else if(param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                            submissionObj = processForm(submissionObj, submitMode);
                            // no properties are specified. note that ngee tropics resources will always be set
                            // submit will also be present, which will be removed in the createDraft method
                            if(Object.keys(submissionObj).length > 2) { 
                                createDraft(submissionObj, submitMode);
                            }
                            else {
                                alert('Please enter a unique name for your new draft');
                            }
                        }
                        else if(status.url) {
                            if(!submissionObj[param] && param == 'authors') {
                                submissionObj[param] = [];
                                submissionObj[param].push(status.url);
                            }
                            else if(param == 'contact') {
                                submissionObj[param] = status.url;
                            }
                            else if(param == 'authors') {
                                submissionObj[param].push(status.url);
                            }
                            entryCount++;
                        }
                        else {
                            alert('There was a problem creating the new entry. Please try again');
                        }
                    });

                });
            }

            else {
                alert('Please enter first and last names for all new contacts/authors');
            }
        }
        else {
            submissionObj = processForm(submissionObj, submitMode);
            if(Object.keys(submissionObj).length > 2) {
                createDraft(submissionObj, submitMode);
            }
            else {
                alert('Please enter a unique name for your new draft');
            }
        }
        
    });

    $('body').on('click', '.js-edit-dataset', function(event) {
        event.preventDefault();
        var url = $('.js-edit-form').attr('data-url');
        var submissionObj = {};


        /*$('.js-edit-form .js-param').each(function() {
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
        });*/

        submissionObj = processForm(submissionObj, false, true);

        console.log(submissionObj);

        $.when(editDataset(submissionObj, url)).done(function(data) {
            if(data) {
                alert('Your changes were successfully saved.');
            }
            else {
                alert('There was an error with the update. Please try again.');
            }
        });
    });

    $('body').on('click', '.js-create-contact', function(event) {
        event.preventDefault();
        var status = createContact($('.js-contact-fname').val(), $('.js-contact-lname').val(), $('.js-contact-email').val(), $('.js-contact-institute').val());
        if(status) {
            alert('Contact successfully created');
        }
        else {
            alert('Fail');
        }
    });

    $('body').on('click', '.js-get-datasets', function(event) {
        event.preventDefault();
        
    });

    $('body').on('click', '.js-del-param', function(event) {
        $(this).closest('section').remove();
    });

    $('body').on('click', '.js-view-dataset', function(event) {
        event.preventDefault();
        var index = $(this).attr('data-index');
        var url = $(this).attr('data-url');

        $.when(getDataSets(url)).done(function(datasetObj) {
            console.log(datasetObj);
            $('#myModal #modalTitle').html('')
                                    .html('<div class="row js-title-row"><div class="columns small-12 medium-9">' + dataObj.datasets[index]['name'] + '</div><div class="columns small-12 medium-3 js-download-wrapper download-wrapper"></div></div>');
            $('#myModal .js-modal-body').html('');
                var inputString = '';
                /*var editForm = $('.js-create-form.dataset').clone()
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
                });*/
                
                for(var prop in datasetObj) {
                    if(!templates.datasets[prop].read_only) {
                        var substring = '<div class="row">';
                        substring += '<div class="columns small-12 medium-3"><b class="js-param-name">' + templates.datasets[prop].label + '</b>' + '&nbsp;</div>';
                        if((prop == 'contact' || prop == 'sites' || prop == 'plots' || prop == 'authors' || prop == 'variables') &&  datasetObj[prop] != null) {
                            console.log('url:' + prop);
                            if(prop == 'contact' || prop == 'authors') {
                                for(var i=0;i<dataObj.contacts.length;i++) {

                                    if(datasetObj[prop].indexOf(dataObj.contacts[i].url) != -1) {
                                        substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.contacts[i].first_name + ' ' + dataObj.contacts[i].last_name + '</span></div>';
                                        
                                    }
                                }
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }
                            else if(prop == 'sites') {
                                for(var i=0;i<dataObj.sites.length;i++) {
                                    if(datasetObj[prop].indexOf(dataObj.sites[i].url) != -1) {
                                        substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.sites[i].site_id + ': ' + dataObj.sites[i].name + '</span></div>';
                                        
                                    }
                                }
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }

                            else if(prop == 'plots') {
                                for(var i=0;i<dataObj.plots.length;i++) {
                                    if(datasetObj[prop].indexOf(dataObj.plots[i].url) != -1) {
                                        substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.plots[i].plot_id + ': ' + dataObj.plots[i].name + '</span></div>';
                                        
                                    }
                                }
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }

                            else if(prop == 'variables') {
                                for(var i=0;i<dataObj.sites.length;i++) {
                                    if(datasetObj[prop].indexOf(dataObj.variables[i].url) != -1) {
                                        substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + dataObj.variables[i].name + '</span></div>';
                                        
                                    }
                                }
                                $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                            }
                        }
                        else if(prop == 'access_level') {
                            for(var k=0;k<templates.datasets.access_level.choices.length;k++) {
                                if(datasetObj[prop] == templates.datasets.access_level.choices[k].value) {
                                    substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + templates.datasets.access_level.choices[k].display_name + '</span></div>';
                                    $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                                }
                            }
                        }
                        else {
                            substring += '<div class="columns small-12 medium-9"><span class="js-param-val">' + (datasetObj[prop] == null ? 'N/A' : datasetObj[prop]) + '</span></div>';
                            $('#myModal .js-modal-body').append($('</div><div/>').append(substring).addClass('js-dataset-row dataset-row'));
                        }
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

                if(dataObj.datasets[index]['archive']) {                       
                    $('.js-file-download-btn').attr('data-url', dataObj.datasets[index]['url'])
                                        .attr('data-archive', dataObj.datasets[index]['archive'])
                                        .attr('href', dataObj.datasets[index]['archive'])
                                        .clone()
                                        .appendTo('.js-download-wrapper')
                                        .addClass('pull-right')
                                        .removeClass('hide');
                }

            //}
            popup.open();
        });
    
    });

    $('body').on('click', '.js-close-modal', function(event) {
        event.preventDefault();
        popup.close();
    });

    $('body').on('click', '.js-get-sites', function(event) {
        event.preventDefault();
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
   
    $('body').on('click', '.js-get-plots', function(event) {
        event.preventDefault();
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

    $('body').on('click', '.js-add-new', function(event) {
        event.preventDefault();
        var input = $(this).closest('.js-param').find('.js-multi-container').first().clone();
        $(input).val('')
            .prop('checked');
        if(input.attr('data-list') == 'contacts') {
            input.find('.js-new-value').addClass('hide').removeClass('js-input');
            input.find('.js-first-name').val('');
            input.find('.js-last-name').val('');
        }
        input.insertBefore(this);
    });

});

function populateDatasets(filter, container) {

}

function createDraft(submissionObj, submitMode) {
    if(submissionObj.submit) {
        delete submissionObj.submit;
        $.when(createDataset(submissionObj)).done(function(status) {
            if(status) {
                if(fileToUpload) {
                    if(fileTypeAllowed(fileToUpload.type) > -1) {
                        var csrftoken = getCookie('csrftoken');

                        $.ajaxSetup({
                            beforeSend: function(xhr, settings) {
                                xhr.setRequestHeader("X-CSRFToken", csrftoken);
                            }
                        });

                        var data = {
                            attachment: fileToUpload
                        };

                        var formData = new FormData();
                        formData.append('attachment', fileToUpload);

                        //data = JSON.parse(data);

                        $.ajax({
                            method: "POST",
                            contentType: false,
                            data: formData,
                            processData: false,
                            url: status.url + "upload/",
                            success: function(data) {
                                if(submitMode) {
                                    $.when(submitDataset(status.url)).done(function(submitStatus) {
                                        alert(submitStatus.detail);
                                        $('.js-clear-form').trigger('click');
                                    });
                                }
                                else {
                                    alert('Draft has been created with the attached file');
                                    $('.js-clear-form').trigger('click');
                                }
                                
                            },

                            fail: function(data) {
                                var detailObj = JSON.parse(data.responseText);
                                alert('Fail: The draft was created successfully but the file could not be uploaded. ' + detailObj.detail);
                            },

                            error: function(data, errorThrown) {
                                var detailObj = JSON.parse(data.responseText);
                                alert('Error: The draft was created successfully but the file could not be uploaded. ' + detailObj.detail);
                            },

                        });

                    }
                    else {
                        alert('Invalid file format. Please upload an archive file');
                    }
                }
                else {
                    if(submitMode) {
                        $.when(submitDataset(status.url)).done(function(submitStatus) {
                            alert(submitStatus.detail);
                            $('.js-clear-form').trigger('click');
                        });
                    }
                    else {
                        alert('Dataset successfully created.');
                        $('.js-clear-form').trigger('click');
                    }
                }
            }
            else {
                alert('There was an error creating the draft. Please try again later.');
            }

        });

    }
    else {
        alert('Please fill all the required fields');
        $('body').animate({
            scrollTop: $('.js-create-form').offset().top
        }, 500);
    }
}

function processForm(submissionObj, submitMode, editMode) {
    var params = $('.js-create-form .js-param');

    if(editMode) {
        params = $('.js-edit-form .js-param');
    }

    params.each(function() {
        var param = $(this).attr('data-param');
        var required = $(this).hasClass('required');
        var multi = $(this).hasClass('multi')

        $(this).find('.js-input').each(function() {
            if($(this).val() != null) {
                if($(this).val().trim()) {
                    if($(this).hasClass('js-new-value')) {
                        ;
                    }
                    else if($(this).hasClass('switch-input')) {
                        if($(this).prop('checked')) {
                            submissionObj[param] = true;
                        }
                        else {
                            submissionObj[param] = false;
                        }
                    }
                    else if(multi) {
                        if(!submissionObj[param]) {
                            submissionObj[param] = [];
                        }
                        submissionObj[param].push($(this).val().trim());
                    }
                    else {
                        submissionObj[param] = $(this).val().trim();
                    }
                }

                else if(submitMode && required) {
                    if($(this).hasClass('js-new-value') && submissionObj[param]) {
                        ;
                    }
                    else {
                        submissionObj.submit = false;
                        $(this).closest('.js-param').addClass('missing');
                    }
                }

            }

            else if ($(this).val() == null && submitMode && required) {
                submissionObj.submit = false;
                $(this).closest('.js-param').addClass('missing');
            }
            
        });
    });

    return submissionObj;
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
            paramHTML = $('<div class="js-param ' + (templates[templateType][param].required ? ' required ' : '') + (templates[templateType][param].multiple ? ' multi ' : '') + ' param"></div>').addClass(param)
                        .attr('data-param', param);
            var label = templates[templateType][param].label;
            if(templates[templateType][param].required) {
                label += '<i class="required">*</i>';
            }

            var tooltip = '<b class="desc-tooltip js-tooltip" title="' + templates[templateType][param].description + '" > ?</b>';

            paramHTML.append($('<span class="js-display-name display-name"></span>').html(label + '&nbsp;&nbsp;' + tooltip));
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
                //var tag = $();
                console.log(list);
                $('.js-ref-list[data-list="' + list + '"]').clone().removeClass('hide').appendTo(paramHTML);
                break;

                default:
                var tag = $('<textarea/>').addClass('js-input');
                paramHTML.append(tag);
                break;
            }

            if(templates[templateType][param].multiple) {
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
    $('.js-input.date').datepicker({
        dateFormat: "yy-mm-dd"
    });
    $( document ).tooltip();
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

/*function createContact(fname, lname, email, institute) {
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
    /*var csrftoken = getCookie('csrftoken');

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
}*/

function createContact(fname, lname, email, institute) {
    var deferObj = jQuery.Deferred();
    var data = { "first_name": fname,
        "last_name": lname,
        "email": email,
        "institution_affiliation": institute };
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
        success: function(data) {
            dataObj.filetypes = data.detail_routes.upload.parameters.attachment.allowed_mime_types;
        },
        fail: function(data) {
            deferObj.resolve(false);
        },

        error: function(data, errorThrown) {
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

function submitDataset(url) {
    var csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });

    var deferObj = jQuery.Deferred();
    $.ajax({
        method: "GET",
        url: url + 'submit/',
        dataType: "json",
        success: function(data) {
            deferObj.resolve(data);
        },

        fail: function(data) {
            deferObj.resolve(data);
        },

        error: function(data, errorThrown) {
            deferObj.resolve(data);
        },

    });

    return deferObj.promise();   
}
