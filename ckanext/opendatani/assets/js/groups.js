$(document).ready(function(){
  var defaults  = {

    exclude: [ 'rgb(0,0,0)', 'rgba(255,255,255)', 'rgb(255,255,255)' ],
    yiqThreshold: 200,
   
  };
  $.adaptiveBackground.run(defaults)

});
