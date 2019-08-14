;(function () {
  var links = document.getElementsByTagName('a');
  
  for (var i = 0; i < links.length; i++) {
    var url = new URL(links[i].href);
    if (url.host !== window.location.host) {
      links[i].setAttribute('target', '_blank');
    }
  }

})();