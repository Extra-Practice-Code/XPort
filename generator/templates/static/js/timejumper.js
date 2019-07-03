(function () {
  var timecodes = document.querySelectorAll('.timecode'),
      player = document.querySelector('main audio');
  
  if (player) {
    for (var i = 0; i < timecodes.length; i++) {
      timecodes[i].addEventListener('click', function () {
        console.log('Jumping to ', parseInt(this.dataset.time));
        player.currentTime = parseInt(this.dataset.time);
      });
    }
  }

})();