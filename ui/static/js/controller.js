uploadApp.controller('UploadCtrl', function ($scope, uploadService, $routeParams, $location, $route, $filter, $resource, $http, $compile) {
    $.when(uploadService.getDatasets()).done(function(data) {
        console.log(data);
        $scope.data = data;
    });
});