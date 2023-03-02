(function () {

  // Add listener to the window to listen to other players starting,
  // to kill this one.

/**
 * Transform time in seconds to timecode: (hh:?)mm:ss
 * @param {number} t time
 */
 function toTimecode (t) {
  t = Math.round(t)
  var hours = Math.floor(t / 3600),
      minutes = Math.floor((t % 3600) / 60),
      seconds = t % 60,
      timecode = '';

  if (hours  > 0) {
      timecode += hours.toString(10)
      timecode += ':';
  }
  
  timecode += (minutes > 9) ? minutes.toString(10) : '0' + minutes.toString(10)
  timecode += ':' + ((seconds > 9) ? seconds.toString(10) : '0' + seconds.toString(10))

  return timecode;
}

  var STATE_INITIAL = 'initial',
      STATE_PAUSED = 'paused',
      STATE_PLAYING = 'playing',
      STATE_LOADING = 'loading',
      PLAYER_DIRECTION_HORIZONTAL = 'horizontal',
      PLAYER_DIRECTION_VERTICAL = 'vertical';

  var InlinePlayer = function (el) {
    this.el = el;
    this.els = {
      media: el.querySelector('audio'),
      playPauseButton: el.querySelector('.button--play-pause'),
      currentTime: el.querySelector('.label--currentTime'),
      skipBackwardButton: el.querySelector('.button--skip-backward'),
      skipForwardButton: el.querySelector('.button--skip-forward'),
      track: el.querySelector('.track'),
      trackProgress: el.querySelector('.track--progress'),
      scrubber: el.querySelector('.track--scrubber')
    };
    this.state = {
      player:  {
        state: STATE_INITIAL,
        playing: false,
        currentTime: 0,
        scrubbing: false,
        scrubbingStart: 0,
        scrubberOffset: 0,
        progressSize: 0,
        trackSize: 0,
        direction: PLAYER_DIRECTION_HORIZONTAL
      },
      media: {
        duration: 0
      },
      currentTimeLabel: '',
      skipForwardAmount: 10,
      skipBackwardAmount: -10,
    };
    this.addEventListeners();
    this.initPlayer();
  }

  InlinePlayer.prototype = {
    addEventListeners: function () {
      this.els.media.addEventListener('play', function () {
        this.state.player.playing = !this.els.media.paused;
        this.setPlayerState(STATE_PLAYING);
      }.bind(this));

      this.els.media.addEventListener('pause', function () {
        this.state.player.playing = !this.els.media.paused;
        this.setPlayerState(STATE_PAUSED);
      }.bind(this));

      this.els.media.addEventListener('waiting', function () {
        this.setPlayerState(STATE_LOADING);
      }.bind(this));

      this.els.media.addEventListener('loadstart',  function () {
        this.setPlayerState(STATE_LOADING);
      }.bind(this));

      this.els.media.addEventListener('durationchange', this.setDuration.bind(this));

      if (this.els.currentTime) {
        this.els.media.addEventListener('timeupdate', this.setCurrentTime.bind(this));
      }

      if (this.els.playPauseButton) {
        this.els.playPauseButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopImmediatePropagation();
          if (this.state.player.state == STATE_INITIAL || this.state.player.state == STATE_PAUSED) {
            this.play();
          } else {
            this.pause();
          }
        }.bind(this));
      }

      if (this.els.skipBackwardButton) {
        this.els.skipBackwardButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopImmediatePropagation();
          this.skip(this.state.skipBackwardAmount);
        }.bind(this));
      }

      if (this.els.skipForwardButton) {
        this.els.skipForwardButton.addEventListener('click', function (e) {
          e.preventDefault();
          e.stopImmediatePropagation();
          this.skip(this.state.skipForwardAmount);
        }.bind(this));
      }

      if (this.els.track && this.els.scrubber) {
        // Listeners to capture movement on the body
        document.body.addEventListener('touchmove', this.updateScrubbing.bind(this), { passive: false });
        document.body.addEventListener('mousemove', this.updateScrubbing.bind(this));
        document.body.addEventListener('touchend', this.finishScrubbing.bind(this), { passive: false });
        document.body.addEventListener('mouseup', this.finishScrubbing.bind(this));
        // Listeners to capture start of scrubbing
        this.els.scrubber.addEventListener('touchstart', this.startScrubbing.bind(this));
        this.els.scrubber.addEventListener('mousedown', this.startScrubbing.bind(this));
      }
    },

    initPlayer: function () {
      this.state.player.currentTime = this.els.media.currentTime;
      this.state.media.duration = this.els.media.duration;
      this.state.player.playing = !this.els.media.paused;
      this.els.media.volume = 1;
      this.el.dataset.state = this.state.player.state;
      this.el.dataset.playing = this.state.player.playing;

      if (this.els.track) {
        var trackSizeObserver = new ResizeObserver(this.updateTrackSize.bind(this));
        trackSizeObserver.observe(this.els.track);
        this.updateTrackSize();
      }

      this.setCurrentTimeLabel();
    },

    setPlayerState: function (nextState) {
      this.state.player.state = nextState;
      this.el.dataset.state = this.state.player.state;
      this.el.dataset.playing = this.state.player.playing;
    },

    play: function () {
      this.els.media.play();
    },

    pause: function () {
      this.els.media.pause();
    },

    seek: function (timecode) {
      this.els.media.currentTime = timecode;
    },

    setCurrentTime: function () {
      this.state.player.currentTime = this.els.media.currentTime;
      this.setCurrentTimeLabel();
      this.updateTrackProgress();
    },

    setDuration: function () {
      this.state.media.duration = this.els.media.duration;
      this.setCurrentTimeLabel();
      this.updateTrackProgress();
    },
 
    updateTrackProgress: function () {
      if (this.els.track && this.els.trackProgress) {
        var nextProgressSize = Math.ceil(this.state.player.trackSize * (this.state.player.currentTime / this.state.media.duration));

        if (nextProgressSize != this.state.player.progressSize) {
          this.state.player.progressSize = nextProgressSize;

          if (this.state.player.direction == PLAYER_DIRECTION_HORIZONTAL) {
            this.els.trackProgress.style.width = nextProgressSize.toString() + 'px';
          }
          else {
            this.els.trackProgress.style.height = nextProgressSize.toString() + 'px';
          }
        }
      }
    },

    updateTrackSize: function () {
      if (this.els.track) {
        var trackRect = this.els.track.getBoundingClientRect();
        if (this.state.player.direction == PLAYER_DIRECTION_HORIZONTAL) {
          this.state.player.trackSize = trackRect.width;
        }
        else {
          this.state.player.trackSize = trackRect.height;
        }
        this.updateTrackProgress();
      }
    },

    setCurrentTimeLabel: function () {
      var nextLabel =  toTimecode(this.state.player.currentTime) + ' / ' + toTimecode(this.state.media.duration);
      
      if (nextLabel != this.state.currentTimeLabel) {
        if (this.els.currentTime) {
          this.els.currentTime.innerText = nextLabel;
        }
        this.state.currentTimeLabel = nextLabel;
      }
    },

    skip: function (amount) {
      var skipTo = Math.max(0, Math.min(this.els.media.currentTime + amount, this.state.media.duration));
      this.els.media.currentTime = skipTo;
    },

    getEventPositionOnDirection: function (e) {
      if (e.type.startsWith('mouse')) {
        if (this.state.player.direction == PLAYER_DIRECTION_HORIZONTAL) {
          return e.clientX;          
        }
        else {
          return e.clientY;
        }
      }

      if (e.type.startsWith('touch')) {
        if (this.state.player.direction == PLAYER_DIRECTION_HORIZONTAL) {
          return e.touches[0].clientX;          
        }
        else {
          return e.touches[0].clientY;
        }
      }
    },

    startScrubbing: function (e) {
      e.stopImmediatePropagation();
      e.preventDefault();
      this.state.player.scrubbing = true;
      this.el.dataset.scrubbing = true;
      console.log(e, e.type);
      this.state.player.scrubbingStart = this.getEventPositionOnDirection(e);
    },

    getOffsetToScrubberPosition (position) {
      return Math.max(
        -1 * this.state.player.progressSize,
        Math.min(
          this.state.player.trackSize - this.state.player.progressSize,
          position - this.state.player.scrubbingStart));
    },

    updateScrubbing: function (e) {
      if (this.state.player.scrubbing) {
        e.preventDefault();
        e.stopImmediatePropagation();
        var offset = this.getOffsetToScrubberPosition(this.getEventPositionOnDirection(e));
        this.setScrubberOffset(offset);
      }
    },

    setScrubberOffset: function (offset) {
      this.state.player.scrubberOffset = offset;
      if (this.state.player.direction == PLAYER_DIRECTION_HORIZONTAL) {
        this.els.scrubber.style.transform = 'translateX(' + offset + 'px)';
      }
      else {
        this.els.scrubber.style.transform = 'translateY(' + offset + 'px)';
      }
    },

    finishScrubbing: function (e) {
      if (this.state.player.scrubbing) {
        e.preventDefault();
        e.stopImmediatePropagation();
        delete this.el.dataset.scrubbing;
        this.state.player.scrubbing = false;
        var newPosition = this.state.player.progressSize + this.state.player.scrubberOffset,
            newTimecode = this.state.media.duration * (newPosition / this.state.player.trackSize);
        this.setScrubberOffset(0);
        this.seek(newTimecode);
      }
    }
  }

  window.InlinePlayer = InlinePlayer;

})();