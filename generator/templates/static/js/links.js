;(function () {
  var links = document.getElementsByTagName('a');
  
  for (var i = 0; i < links.length; i++) {
    var url = new URL(links[i].href);
    console.log(url, url.host == window.location.host);
    if (url.host !== window.location.host) {
      links[i].setAttribute('target', '_blank');
    }
  }

})();