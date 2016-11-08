var uploadApp = angular.module('uploadApp', ['ngRoute', 'ngResource']);

uploadApp.config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('//');
    $interpolateProvider.endSymbol('//');
  });


uploadApp.service('uploadService', function(){
    this.getDatasets = function() {
        var dfd = jQuery.Deferred();
        $.ajax({
            
            method: "GET",
            url: '/api/v1/datasets/',
            dataType: "json",
            success: function(data) {
                dfd.resolve(data);
            },

            fail: function(data) {
                dfd.resolve(false);
            },

            error: function(data, errorThrown) {
                dfd.resolve(false);
            },

            timeout: 30000

        });

        return dfd.promise();
    };
});