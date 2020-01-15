(function () {
  var entries = NodeList
      eventCache = {};
  
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
    if (history.pushState) {
      if (hash) {
        history.pushState(null, null, location.pathname + '#' + hash);
      }
      else {
        history.pushState(null, null, location.pathname);
      }
    }
    else {
      location.hash = hash;
    }
  }

  function showImage(path) {
    var map = document.getElementById('map');
    if (path && path.toLowerCase() == 'none') {
      path = null;
    }
    if (path) {
      map.style.backgroundImage = 'url(' + path + ')';
      delete map.dataset.hidden;
    }
    else {
      map.style.backgroundImage = '';
      map.dataset.hidden = true;
    }
  }

  function activate(entry, entries) {
    for (var e = 0; e < entries.length; e++) {
      delete entries[e].dataset.active;
    }

    entry.dataset.active = 'true';
    var container = document.querySelector('aside.home.event-detail');
    container.dataset.loading = 'true';
    container.innerHTML = '';
    showImage(entry.dataset.image);

    if (entry.id in eventCache) {
      delete container.dataset.loading;
      container.innerHTML = eventCache[entry.id];
      setImageListeners();
      container.querySelector('[data-role="close"]').addEventListener('click', close);
    } else {
      fetch('/api/activities/' + entry.id + '.html', {
        method: "GET"
      }).then(function (response) {
        if (response.ok) {
          response.text().then(function (text) {
            delete container.dataset.loading;
            eventCache[entry.id] = text;
            container.innerHTML = text;
            setImageListeners();
            container.querySelector('[data-role="close"]').addEventListener('click', close);
          });
        }
      });
    }

  }

  function close () {
    setHash(null);
    document.body.classList.remove('event-active-through-click', 'aside-active-through-click');
  }

  function show(entry, entries) {
    document.body.classList.add('event-active-through-click', 'aside-active-through-click');
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

  function unwrap (node) {
    var parent = node.parentElement;
    while (node.firstChild) {
      parent.insertBefore(node.firstChild, node);
    }
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
      document.body.classList.remove('event-active-through-click', 'aside-active-through-click');
    }
  };

  window.addEventListener('load', function () {
    entries = document.querySelectorAll('.event-list .event');
    
    for (var i = 0; i < entries.length; i++) {
      unwrap(entries[i].querySelector('h2 a'))
      unwrap(entries[i].querySelector('time a'));

      (function (entry, entries) {
        entry.addEventListener('click', function () {
          setHash(entry.id);
          show(entry, entries);
        });
      })(entries[i], entries);
    }
  });
})();