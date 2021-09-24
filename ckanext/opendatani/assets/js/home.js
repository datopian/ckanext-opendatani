$(document).ready(function(){
  var defaults  = {

    exclude: [ 'rgb(0,0,0)', 'rgba(255,255,255)', 'rgb(255,255,255)' ],
    yiqThreshold: 200,
    parent: '.group',
   
  };
  $.adaptiveBackground.run(defaults)


  // twitter
  twitterFetcher.fetch({
    "profile": {"screenName": 'opendatani'},
    "domId": 'tweets',
    "maxTweets": 5,
    "enableLinks": true,
    "customCallback":handleTweets,
  });
  
  
  function handleTweets(tweets){
    var i=0;
    var j=tweets.length;
    var l="<ul class='carousel-inner'>";
    while(i<j){
      l+="<li class='item' id='tweet"+i+"'>"+tweets[i]+"</li>";
      i++;
    }
    l+="</ul>";
    document.getElementById("tweets").innerHTML=l;
    var n=(j-1);
    
    $( "#tweet0" ).addClass( "active" );
    
    $('.carousel').carousel({
      interval: 10000
    })
  } 
  
});