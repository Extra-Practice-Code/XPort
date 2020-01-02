(function () {
  var entries = NodeList;
  
  // var eventCloseButton = document.querySelector('#detail-container .close-button');
  // eventCloseButton.addEventListener('click', function () {
  //   setHash(null);
  //   document.body.className = document.body.className.replace(/\s*event-active-through-click/, '');
  // });

  function setImageListeners () {
    var images = document.querySelectorAll('aside.home.event-detail img');

    for (var i=0; i < images.length; i++) {
      images[i].addEventListener('click', function () {
        if (this.parentElement && this.parentElement.tagName.toLowerCase() == 'figure') {
          this.parentElement.classList.toggle('full');
        } else {
          this.classList.toggle('full');
        }
      })
    }
  };

  function setHash(hash) {
    if (hash) {
      hash = '#' + hash;
    }
    else {
      hash = '/';
    }

    if (history.pushState) {
      history.pushState(null, null, hash);
    }
    else {
      location.hash = hash;
    }
  }

  function showImage(path) {
    var holder = document.getElementById('prolog');
    if (path && path != 'None') {
      holder.style.backgroundImage = 'url(' + path + ')';
    } else {
      holder.style.removeProperty('background-image');
    }
  }

  function activate(entry, entries) {
    for (var e = 0; e < entries.length; e++) {
      delete entries[e].dataset.active;
    }

    entry.dataset.active = 'true';
    var container = document.querySelector('aside.home.event-detail');

    fetch('/api/activities/' + entry.id + '.html', {
      method: "GET"
    }).then(function (response) {
      if (response.ok) {
        response.text().then(function (text) {
          container.innerHTML = text;
          setImageListeners();
        });
      }
    });
  }

  function show(entry, entries) {
    document.body.className += ' event-active-through-click';
    activate(entry, entries);
  }

  function getEntryByHash(hash) {
    var id = window.location.hash.substr(1);
    var entry = document.getElementById(id);

    if (entry && entry.className.indexOf('event') > -1) {
      return entry;
    }

    return false
  }

  if (window.location.hash) {
    var entry = getEntryByHash(window.location.hash);

    if (entry) {
      show(entry, entries);
    }
  }

  window.onhashchange = function () {
    var entry = getEntryByHash(window.location.hash);

    if (entry) {
      show(entry, entries);
    } else {
      document.body.className = document.body.className.replace(/\s*event-active-through-click/, '');
    }
  };

  window.addEventListener('load', function () {
    entries = document.querySelectorAll('.event-list .event');
    
    for (var i = 0; i < entries.length; i++) {
      (function (entry, entries) {
        entry.addEventListener('click', function () {
          setHash(entry.id);
          show(entry, entries)
        });
      })(entries[i], entries);
    }
  });
})();